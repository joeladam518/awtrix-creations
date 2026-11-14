# AWTRIX creations

Scripts, flows and icons for [AWTRIX NG](https://blueforcer.github.io/awtrix-ng/), shared on the
[AWTRIX Hub (awtrix.de)](https://awtrix.de).

## Packages

| Package | Type | What it does |
|---|---|---|
| [BigClock](packages/big-clock/) | Script | The biggest clock the 52×16 TC002 can show: 16-pixel digits, solid colon, optional seconds and night color |
| [BigDate](packages/big-date/) | Script | The biggest date the 52×16 TC002 can show, in the format you pick, with optional night color |

Each package folder has its own README with install steps and settings.

---

## Releasing a package

**Each package is released on its own**, with its own version. The tag picks the package:

| Tag | Releases |
|---|---|
| `big-clock-v1.2.0` | `packages/big-clock` at version 1.2.0 |
| `big-date-v2.0.0` | `packages/big-date` at version 2.0.0 |

1. **Bump the version** in the package. For a script, that's the `# @version` line in its `.ax` file.
2. Merge to `main`.
3. **Create a GitHub release** with a tag like `big-clock-v1.2.0`.
4. The [release workflow](.github/workflows/release.yml) builds that package and attaches
   `big-clock-1.2.0.zip` to the release.
5. **Upload to awtrix.de by hand** (the Hub has no upload API). The zip holds everything the Hub's form
   asks for: the file to upload, `preview.png` for the cover, and the README for the description.

**The tag version must match the package version exactly.** If it doesn't, the workflow fails and
attaches nothing. `v1.0` and `v1.0.0` count as different.

## Adding a package

1. Make a folder in `packages/`, named in kebab-case (`big-clock`). The folder name is the tag prefix.
2. Add the files, a `README.md`, and optionally a `preview.png`.
3. Add an `awtrix.json` manifest (below).
4. Run `python3 tools/build.py --check` to validate.
5. Add a row to the table above.

### `awtrix.json`

Tells the build what the package is and what goes in its zip.

```json
{
  "type": "script",
  "files": ["BigClock.ax"],
  "preview": "preview.png"
}
```

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | `script`, `flow` or `icon` |
| `files` | yes | The files to share. A script needs exactly one `.ax` file. |
| `preview` | no | Cover image for the Hub. Added to the zip. |
| `name`, `version` | flows and icons only | Scripts take these from their `# @name` and `# @version` header lines, so they aren't repeated here. |

`README.md` is always added to the zip.

## Building locally

Needs only Python 3.8+.

```sh
python3 tools/build.py                          # validate and zip every package into dist/
python3 tools/build.py --check                  # validate only
python3 tools/build.py --tag big-clock-v1.0     # build one package, as the release does
```

A [check workflow](.github/workflows/check.yml) runs `--check` on every push and pull request.
