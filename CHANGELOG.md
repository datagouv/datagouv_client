# Changelog

## 0.3.1 (2026-05-19)

- CLI: add a `get` method for all objects ([#53](https://github.com/datagouv/datagouv_client/pull/53))
- CLI: allow to remain anonymous when only getting data ([#52](https://github.com/datagouv/datagouv_client/pull/52))
- CLI: fix environment in URI ([#51](https://github.com/datagouv/datagouv_client/pull/51))


## 0.3.0 (2026-05-12)

- Add CLI integration ([#48](https://github.com/datagouv/datagouv_client/pull/48))
- Add `prod` alias for `www` ([#50](https://github.com/datagouv/datagouv_client/pull/50))
- Add a method to sort a dataset's resources ([#45](https://github.com/datagouv/datagouv_client/pull/45))
- Add ability to download resource content buffer and keep it in memory ([#42](https://github.com/datagouv/datagouv_client/pull/42))
- Allow to retrieve data from tabular API ([#39](https://github.com/datagouv/datagouv_client/pull/39))
- Better downloaded file name ([#41](https://github.com/datagouv/datagouv_client/pull/41))
- Better verbose ([#40](https://github.com/datagouv/datagouv_client/pull/40))
- Make `BaseObject` abstract ([#44](https://github.com/datagouv/datagouv_client/pull/44))
- Only publish when commit on main ([#38](https://github.com/datagouv/datagouv_client/pull/38))
- Only publish when tag ([#37](https://github.com/datagouv/datagouv_client/pull/37))
- Rebuild lock ([#46](https://github.com/datagouv/datagouv_client/pull/46))
- Update Python version requirement to include 3.14 ([#43](https://github.com/datagouv/datagouv_client/pull/43))
- fix: tabular url on demo ([#49](https://github.com/datagouv/datagouv_client/pull/49))


## 0.2.3 (2026-01-15)

- Change release process ([#36](https://github.com/datagouv/datagouv_client/pull/36))
- Fix `delete_extras` function ([#35](https://github.com/datagouv/datagouv_client/pull/35))
- Fix resource download ([#34](https://github.com/datagouv/datagouv_client/pull/34))
- Update to version 0.2.3.dev for next development cycle


## 0.2.2 (2025-11-13)

- Fix community resources URIs [#33](https://github.com/datagouv/datagouv_client/pull/33)

## 0.2.1 (2025-11-03)

- Allow to pass kwargs from client and to cast objects from `get_all_from_api_query` [#29](https://github.com/datagouv/datagouv_client/pull/29)
- Add more attributes to objects [#30](https://github.com/datagouv/datagouv_client/pull/30)
- Allow to pass arguments to the client's session and to set timeout [#31](https://github.com/datagouv/datagouv_client/pull/31)

## 0.2.0 (2025-09-19)

- feat: add Topic [#27](https://github.com/datagouv/datagouv_client/pull/27)
- Replace relevant methods with attributes (/!\ breaking changes) and add tests [#27](https://github.com/datagouv/datagouv_client/pull/28)

## 0.1.4 (2025-09-04)

- Add `preview_url` field to resources' attributes [#18](https://github.com/datagouv/datagouv_client/pull/18)
- Pass the organization's client to its datasets [#19](https://github.com/datagouv/datagouv_client/pull/19)
- Switch to `httpx` [#21](https://github.com/datagouv/datagouv_client/pull/21)
- Add metrics [#22](https://github.com/datagouv/datagouv_client/pull/22)
- Accept `Path` type as download arguments, and use `Path` internally to handle file paths [#24](https://github.com/datagouv/datagouv_client/pull/24)

## 0.1.3 (2025-08-21)

- Switch to pyproject [#11](https://github.com/datagouv/datagouv_client/pull/11)
- Upgrade requests for security reasons [#12](https://github.com/datagouv/datagouv_client/pull/12)
- Add more attributes to dataset and resource objects [#13](https://github.com/datagouv/datagouv_client/pull/13)
- Add organization object [#15](https://github.com/datagouv/datagouv_client/pull/15)
- Adapt front URLs to the new standard [#17](https://github.com/datagouv/datagouv_client/pull/17)

## 0.1.1 (2025-06-06)

- Remove dev dependencies from the package and add build metadata [#9](https://github.com/datagouv/datagouv_client/pull/9)

## 0.1.0 (2025-05-14)

- Allow to download a dataset's resources [#8](https://github.com/datagouv/datagouv_client/pull/8)
- Allow to download a resource [#7](https://github.com/datagouv/datagouv_client/pull/7)
- Allow to prevent fetch on object creation [#6](https://github.com/datagouv/datagouv_client/pull/6)
- Allow to update static resources' files [#4](https://github.com/datagouv/datagouv_client/pull/4)
- Polishing after first release [#2](https://github.com/datagouv/datagouv_client/pull/2)
- Package creation [#1](https://github.com/datagouv/datagouv_client/pull/1)
