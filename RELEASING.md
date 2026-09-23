# Releasing

## Where the code lives

The working copy of this package is a folder inside the authors' research
repository, where it sits next to the analysis it was extracted from. This
repository is that folder pushed out on its own, so its history is the history
of the folder and not of the wider project. Nothing is edited here directly.

To push the folder out after changing it in the working repository:

```bash
git subtree push --prefix=snowreach github main
```

with `github` a remote pointing at this repository. The first time:

```bash
git remote add github git@github.com:<owner>/snowreach.git
git subtree push --prefix=snowreach github main
```

`git subtree` rewrites the commits that touch the folder into a history of
their own, so the result is a normal repository and not a submodule. It
reads the same commits every time, which makes the push slow on a long
history but never wrong. To see what would go out without pushing:

```bash
git subtree split --prefix=snowreach --rejoin
```

## Repository metadata

The GitHub *About* field, which is what shows under the title and in search
results, and is capped at 350 characters:

> Virga classification and blind-zone simulation for vertically pointing
> radars. Separates the snow that reaches the ground from the snow that
> sublimates below a satellite's lowest observable height, and measures what
> that costs in occurrence and in accumulation.

It opens on what the package does rather than on the question the README
opens with, because someone searching for "virga classification" or "blind
zone" needs to see those words first. The paper is not in it: GitHub renders
`CITATION.cff` as a *Cite this repository* button, so it would take space
without adding anything.

Topics: `radar`, `snowfall`, `antarctica`, `virga`, `precipitation`,
`remote-sensing`, `cloudsat`, `earthcare`, `micro-rain-radar`, `xarray`.

## Cutting a release

Zenodo archives this repository on every GitHub release, and mints a DOI for
it. The metadata come from `.zenodo.json` at the root, which overrides what
Zenodo would otherwise guess from the GitHub API: the authors with their
ORCIDs, the licence, the keywords and the related identifiers. Its `doi`
field, if one were added, would have no effect, because Zenodo assigns the
DOI itself.

1. Bump `__version__` in `snowreach/__init__.py` and `version` in
   `.zenodo.json`. They must agree.
2. Update `CITATION.cff` if the author list or the paper's status changed.
3. Push the folder out with `git subtree push`.
4. On GitHub, draft a release with the tag `vX.Y.Z`. Zenodo ingests it and
   publishes a new version of the record, under the same concept DOI.
5. Put the new version DOI wherever it is cited.

The integration archives the repository as it stands at the tag, so anything
not committed is not in the deposit. That is why the example month is a
tracked file rather than something copied in at packaging time, and why this
folder carries a `.gitattributes` that keeps it out of Git LFS: an LFS
pointer would travel instead of the data.

## A record cannot be linked afterwards

Zenodo cannot attach a GitHub repository to a record that already exists. A
manual deposit and a release-born one are two records with two concept DOIs
and no way to merge them. If this package is ever deposited by hand as well,
that is a second, separate record, and it should be avoided.

`make_release.py` builds a standalone zip of the same files. It predates the
GitHub route and is not how releases are made. It is still the way to hand
someone a self-contained copy without a clone.
