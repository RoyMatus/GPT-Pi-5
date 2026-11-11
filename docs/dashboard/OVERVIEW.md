# Overview policy

One shared clock/timezone service and registered Computer/Markets hooks supply all
summaries. No alternate SSH connection, quote poller or model data attachment exists.
Summary links open the exact selected instrument/detail screen. Missing values remain
unavailable; zero temperature is a reading. Source/acquisition times are accessible.

Weather uses Open-Meteo's free noncommercial endpoint, attributed under CC BY 4.0.
Official references checked: https://open-meteo.com/en/docs ;
https://open-meteo.com/en/docs/geocoding-api ; https://open-meteo.com/en/pricing .
This personal prototype does not enable paid/commercial service. Moscow is an explicit
named default, not inferred current location. Search shows choices; selection is RAM
session-only, no geolocation permission or IP geolocation. Chosen locality is sent to
Open-Meteo only. The value is model forecast, not a local sensor/observational reading.

Shared forecast cache: 10 minutes, 64 locations max, 256 KB response bound, 10-second
network deadline. Errors back off 30 seconds; cached values become visibly stale.
Clock and other widgets never wait for weather. Search is bounded/rate limited.

Base 3049fb98501167fd347fcb6974c16a0bea7fe357. Coordinator root owns Overview plus
exclusive app/session-read helper, registry/routes, shell CSS, shared browser-fixture
boundary, affected voice/market/computer browser runners and CI/docs until handoff.
No parallel shared-file writer. Tests use synthetic provider transports, including
unrelated screens visited by voice tests. Live weather reachability is checked separately.
Browser verification covers one guest identity at boot, matching summary/detail values,
links and city selection; physical touch/final full-screen comparison remain separate.
