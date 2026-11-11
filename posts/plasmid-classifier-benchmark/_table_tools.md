| Tool | Version | Input | Settings | Database or model | Contigs decided |
|---|---|---|---|---|---:|
| Platon [@platon] | 1.6 | Contigs | Default settings | Platon database v1.5.0 ([link](https://doi.org/10.5281/zenodo.4066768)) | 100.0% |
| gplas2 [@plasmidec] | 1.1.0 | Assembly graph | PlasmidEC predictions (*E. coli* preset) as the initial classification; default settings | None | 88.7% |
| PlasmidEC [@plasmidec] | 1.3 | Assembly graph | *E. coli* preset: Centrifuge, Platon and RFPlasmid (Enterobacteriaceae model), majority vote | PlaScope *E. coli* database v1.1; Platon database v1.5.0 | 100.0% |
| MOB-recon [@mobsuite] | 3.1.7 | Contigs | Default settings | Database bundled in the MOB-suite 3.1.7 container | 99.1% |
| plASgraph2 [@plasgraph2] | 1.0.0 (commit 7bc4e92) | Assembly graph | Default settings | ESKAPEE model distributed with plASgraph2 1.0.0 | 96.0% |
| HyAsP [@hyasp] | 1.0.0 | Assembly graph | Maximum plasmid length 750 kb; otherwise default settings | HyAsP NCBI RefSeq database ([link](https://doi.org/10.6084/m9.figshare.8001827.v1)) | 100.0% |
| RFPlasmid [@rfplasmid] | 0.0.18 | Contigs | Enterobacteriaceae model; Jellyfish k-mer counting | Models distributed with RFPlasmid 0.0.18 | 100.0% |
| Plasmer [@plasmer] | 0.1 | Contigs | Minimum length 0 bp; chromosome length threshold 100 Mb | Plasmer database v1.0 ([link](https://doi.org/10.5281/zenodo.7030675)) | 100.0% |
| PlaScope [@plascope; @centrifuge] | Centrifuge 1.0.4 | Contigs | Up to 1,000 assignments per contig | PlaScope *E. coli* database v1.1 ([link](https://doi.org/10.5281/zenodo.1311641)) | 97.0% |
| PLASMe [@plasme] | 1.1 (commit ef0409b) | Contigs | Coverage 0.9, identity 0.9, probability 0.5 | PLASMe database ([link](https://doi.org/10.5281/zenodo.8046934)) | 100.0% |
| geNomad [@genomad] | 1.7.1 | Contigs | End-to-end workflow; default settings | geNomad database v1.5 ([link](https://doi.org/10.5281/zenodo.8339387)) | 100.0% |
| PlasmidFinder [@plasmidfinder] | 2.0.1 | Contigs | BLAST method; default thresholds | PlasmidFinder database 2.2.0 (commit 49c24c1) | 99.6% |
