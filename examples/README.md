# examples/

Public, synthetic (non-proprietary) instance data for the TwinShip ontology.

This is the opposite of [`data/`](../data/README.md): everything here is tracked and
committed normally. Use this folder for fictional/synthetic Knowledge Graph (KG)
individuals that are safe to publish alongside the ontology — e.g. demonstrator
vessels, sample component graphs, or data used in documentation and papers.

Do not place real or proprietary vessel data here — that belongs in the gitignored
`data/` folder instead.

## Structure

One subfolder per example/demonstrator, e.g.:

- `futuristic-vessel/` — synthetic KG data for the futuristic (diesel-electric) RoRo
  vessel demonstrator (see `twinship-data-pipeline`'s `futuristic-vessel` extraction
  pipeline for the corresponding component structure).
