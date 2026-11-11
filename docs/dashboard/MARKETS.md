# Markets sources and policy

Private prototype display only; no paid service, trading or account API is enabled.
Kraken public OHLC provides crypto spot candles. MOEX ISS provides delayed exchange
candles for the explicit board/security identity; no realtime entitlement is assumed.
Bank of Russia XML provides official per-unit FX rates, not executable exchange prices.
Each quote retains provider, category, currency, quote time, acquisition time and state.
Oil/metals are explicitly unsupported until a licensed provider and contract identity
are selected; no unrelated instrument is substituted. Exchange IDs are part of identity.

Official references checked 2026-11-11:
- https://docs.kraken.com/api-reference/market-data/get-ohlc-data
- https://www.moex.com/a2920
- https://www.cbr.ru/development/sxml/

A 60-second shared cache/lock bounds refresh; concurrency is three. Failures back off
30 seconds and expose stale cached values or missing values. There is no paid fallback.
Body limit is 512 KB. Period change is from first to last available candle; missing or
zero baselines have no percentage. CBR nominal conversion uses Decimal. Session-only
watchlists support add/remove/reorder and clear at expiry/logout/restart. Public quote
cache is not private account data. Overview consumes the same feature hook/backend cache.

Base 6150fc199b5189eb6349f8ba472d8be025fe9c3a. Coordinator root owns market paths and
exclusive shared webapp Session/routes, registry/client, browser fixture and docs lease
until PR handoff. No competing writer. Offline parser, cache/backoff, independent
summary and HTTP session-isolation tests use synthetic providers. Live provider reachability
is checked separately, never as a CI dependency. Display rights for a commercial/public
redistribution are not established by this personal prototype; no commercial use enabled.
