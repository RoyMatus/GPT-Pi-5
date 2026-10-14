import copy
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError

from tools.github import execute, parser
from tools.github_api import (BASE, Client, GitHubError, NoRedirect, REPOSITORY,
                              credential, merge_pr, validate_checks)

SHA = 'a' * 40
BASE_SHA = 'b' * 40


def ready_pr():
    return {'number': 13, 'state': 'open', 'draft': False, 'merged': False,
            'mergeable': True, 'mergeable_state': 'clean',
            'head': {'sha': SHA},
            'base': {'ref': 'main', 'sha': BASE_SHA, 'repo': {'full_name': REPOSITORY}}}


def successful_checks():
    # Explicit fixture independent of production check-name generation.
    names = ['test (ubuntu-latest, 3.11)', 'test (ubuntu-latest, 3.13)',
             'test (windows-latest, 3.11)', 'test (windows-latest, 3.13)']
    return [{'name': name, 'head_sha': SHA, 'status': 'completed',
             'conclusion': 'success', 'app': {'slug': 'github-actions'}} for name in names]


class MergeClient:
    def __init__(self):
        self.pr = ready_pr()
        self.checks = successful_checks()
        self.statuses = []
        self.writes = []
        self.base_reads = 0
        self.head_reads = 0
        self.change_base = False
        self.change_head = False
        self.confirm_merge = True

    def request(self, method, path, body=None):
        if method == 'PUT':
            self.writes.append((path, body))
            return {'merged': self.confirm_merge, 'sha': 'c' * 40}
        if path == 'git/ref/heads/main':
            self.base_reads += 1
            return {'object': {'sha': 'd' * 40 if self.change_base and self.base_reads > 1 else BASE_SHA}}
        if path == 'pulls/13':
            self.head_reads += 1
            pr = copy.deepcopy(self.pr)
            if self.change_head and self.head_reads > 1:
                pr['head']['sha'] = 'e' * 40
            if self.writes:
                pr['merged'] = self.confirm_merge
            return pr
        raise AssertionError((method, path))

    def collection(self, path, key):
        return self.checks if key == 'check_runs' else self.statuses


class MergeTests(unittest.TestCase):
    def test_merge_binds_expected_sha_and_rechecks_result(self):
        client = MergeClient()
        self.assertTrue(merge_pr(client, 13, SHA)['merged'])
        self.assertEqual([('pulls/13/merge', {'merge_method': 'squash', 'sha': SHA})], client.writes)
        self.assertEqual(3, client.head_reads)

    def test_missing_pending_failed_skipped_wrong_source_and_stale_checks_block(self):
        mutations = [lambda checks: checks.pop(),
                     lambda checks: checks[0].update(status='queued'),
                     lambda checks: checks[0].update(conclusion='failure'),
                     lambda checks: checks[0].update(conclusion='skipped'),
                     lambda checks: checks[0].update(app={'slug': 'untrusted-app'}),
                     lambda checks: checks[0].update(head_sha='f' * 40)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                client = MergeClient()
                mutation(client.checks)
                with self.assertRaises(GitHubError):
                    merge_pr(client, 13, SHA)
                self.assertEqual([], client.writes)

    def test_bad_or_unknown_mergeability_blocks(self):
        for value in (False, None):
            client = MergeClient()
            client.pr['mergeable'] = value
            with self.assertRaises(GitHubError):
                merge_pr(client, 13, SHA)
            self.assertFalse(client.writes)

    def test_wrong_repository_target_draft_closed_or_sha_blocks(self):
        for mutation in (
            lambda pr: pr['base']['repo'].update(full_name='example/other'),
            lambda pr: pr['base'].update(ref='other'),
            lambda pr: pr.update(draft=True),
            lambda pr: pr.update(state='closed'),
            lambda pr: pr['head'].update(sha='f' * 40),
            lambda pr: pr['base'].update(sha='f' * 40),
        ):
            client = MergeClient()
            mutation(client.pr)
            with self.assertRaises(GitHubError):
                merge_pr(client, 13, SHA)
            self.assertFalse(client.writes)

    def test_base_or_head_change_during_checks_blocks(self):
        for flag in ('change_base', 'change_head'):
            client = MergeClient()
            setattr(client, flag, True)
            with self.assertRaises(GitHubError):
                merge_pr(client, 13, SHA)
            self.assertFalse(client.writes)

    def test_failed_additional_status_blocks(self):
        client = MergeClient()
        client.statuses = [{'state': 'failure'}]
        with self.assertRaises(GitHubError):
            merge_pr(client, 13, SHA)
        self.assertFalse(client.writes)

    def test_unconfirmed_write_is_not_reported_success(self):
        client = MergeClient()
        client.confirm_merge = False
        with self.assertRaises(GitHubError):
            merge_pr(client, 13, SHA)
        self.assertEqual(1, len(client.writes))


class CliTests(unittest.TestCase):
    def test_preview_never_initializes_client(self):
        factory = Mock(side_effect=AssertionError('No network or credentials during preview'))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'body.md'
            path.write_text('Synthetic issue body\nSecond line', encoding='utf-8')
            args = parser().parse_args(['issue', 'create', '--title', 'Synthetic title', '--body-file', str(path)])
            result = execute(args, factory)
            self.assertTrue(result['preview'])
            self.assertEqual('Synthetic issue body\nSecond line', result['changes']['body'])
        factory.assert_not_called()

    def test_merge_preview_never_writes(self):
        factory = Mock(side_effect=AssertionError('No network'))
        result = execute(parser().parse_args(['pr', 'merge', '13', '--expected-sha', SHA]), factory)
        self.assertTrue(result['preview'])
        factory.assert_not_called()

    def test_issue_number_cannot_target_pull_request(self):
        client = Mock()
        client.request.return_value = {'number': 13, 'pull_request': {}}
        with self.assertRaises(GitHubError):
            execute(parser().parse_args(['issue', 'update', '13', '--title', 'New', '--apply']), lambda: client)
        self.assertEqual([('GET', 'issues/13')], [call.args for call in client.request.call_args_list])

    def test_update_reads_back_requested_fields(self):
        client = Mock()
        client.request.side_effect = [{'title': 'Before'}, {}, {'title': 'After', 'number': 12}]
        result = execute(parser().parse_args(['issue', 'update', '12', '--title', 'After', '--apply']), lambda: client)
        self.assertEqual('After', result['title'])
        self.assertEqual('GET', client.request.call_args_list[-1].args[0])

    def test_unconfirmed_update_fails_without_retry(self):
        client = Mock()
        client.request.side_effect = [{'title': 'Before'}, {}, {'title': 'Before'}]
        with self.assertRaises(GitHubError):
            execute(parser().parse_args(['issue', 'update', '12', '--title', 'After', '--apply']), lambda: client)
        self.assertEqual(1, sum(c.args[0] == 'PATCH' for c in client.request.call_args_list))

    def test_create_reads_new_object_back(self):
        client = Mock()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'body.md'
            path.write_text('Body', encoding='utf-8')
            client.request.side_effect = [{'number': 15}, {'number': 15, 'title': 'Title', 'body': 'Body'}]
            result = execute(parser().parse_args(['issue', 'create', '--title', 'Title', '--body-file', str(path), '--apply']), lambda: client)
            self.assertEqual(15, result['number'])
            self.assertEqual(('GET', 'issues/15'), client.request.call_args_list[-1].args)

    def test_invalid_arguments_fail_before_network(self):
        for argv in (['issue', 'merge', '13', '--expected-sha', SHA],
                     ['pr', 'merge', '13', '--expected-sha', 'short'],
                     ['issue', 'update', '12'], ['issue', 'inspect', '12', '--apply']):
            factory = Mock()
            with self.assertRaises(GitHubError):
                execute(parser().parse_args(argv), factory)
            factory.assert_not_called()


class TransportTests(unittest.TestCase):
    def test_host_and_traversal_rejected_before_auth(self):
        with patch('tools.github_api.credential', side_effect=AssertionError('No credentials')):
            for path in ('https://evil.example', '//evil.example', '../other', '%2e%2e/other', 'x\\y', 'x#bad'):
                with self.assertRaises(GitHubError):
                    Client().request('GET', path)

    def test_request_uses_only_project_endpoint(self):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value = b'{"number": 12}'
        client = Client('synthetic-token', opener)
        self.assertEqual(12, client.request('GET', 'issues/12')['number'])
        self.assertEqual(BASE + '/issues/12', opener.open.call_args.args[0].full_url)

    def test_redirect_is_refused(self):
        with self.assertRaises(GitHubError):
            NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.example')

    def test_http_error_never_exposes_response_or_token(self):
        opener = Mock()
        opener.open.side_effect = HTTPError(BASE, 403, 'secret-text', {}, io.BytesIO(b'secret-text'))
        with self.assertRaises(GitHubError) as error:
            Client('secret-text', opener).request('GET')
        self.assertNotIn('secret-text', str(error.exception))

    def test_repository_identity_checked(self):
        client = Client('synthetic-token')
        client.request = Mock(return_value={'full_name': 'example/other'})
        with self.assertRaises(GitHubError):
            client.verify_repository()

    def test_pagination_includes_later_failed_check(self):
        client = Client('synthetic-token')
        first = successful_checks() + [dict(successful_checks()[0], name=f'extra-{i}') for i in range(96)]
        later = dict(successful_checks()[0], name='late-check', conclusion='failure')
        client.request = Mock(side_effect=[{'total_count': 101, 'check_runs': first},
                                          {'total_count': 101, 'check_runs': [later]}])
        checks = client.collection('commits/' + SHA + '/check-runs?filter=latest', 'check_runs')
        with self.assertRaises(GitHubError):
            validate_checks(checks, [], SHA)
        self.assertIn('page=2', client.request.call_args.args[1])

    def test_incomplete_pagination_fails_closed(self):
        client = Client('synthetic-token')
        client.request = Mock(return_value={'total_count': 101, 'check_runs': []})
        with self.assertRaises(GitHubError):
            client.collection('checks', 'check_runs')

    def test_env_credential_does_not_invoke_git(self):
        with patch.dict('os.environ', {'GH_TOKEN': 'synthetic-token'}), patch('subprocess.run') as run:
            self.assertEqual('synthetic-token', credential())
            run.assert_not_called()
