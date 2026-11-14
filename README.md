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

## Packaging a release

**Each package has its own version**, so one can be on 1.2.0 while another is on 2.0.0.

1. **Bump the version** in the package. For a script, that's the `# @version` line in its `.ax` file.
2. **Build the zip**, pointing at the package folder with a matching tag:
   ```sh
   python3 tools/build.py packages/big-clock --tag v1.2.0
   ```
   This writes `dist/big-clock-v1.2.0.zip`.
3. **Upload to awtrix.de by hand** (the Hub has no upload API). The zip holds everything the Hub's form
   asks for: the file to upload, `preview.png` for the cover, and the README for the description.

**The tag must match the package version exactly**, or the build stops and writes nothing. The leading
`v` is optional, but `v1.0` and `v1.0.0` count as different.

## Adding a package

1. Make a folder in `packages/`, named in kebab-case (`big-clock`). The folder name starts the zip name.
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

## Build script options

Needs only Python 3.8+. Zips go to `dist/`, which git ignores.

```sh
python3 tools/build.py                                  # zip every package
python3 tools/build.py packages/big-clock --tag v1.0    # zip one package, checking its version
python3 tools/build.py packages/big-clock packages/big-date   # zip several
python3 tools/build.py --check                          # validate only, no zips
```
