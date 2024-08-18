KALI LINUX

- Install pipx
- (run installation commands)
- Ensure spacy compatible with pydantic (spacy 3.4 + latest pydantic)
- NLTK installation
- Wordnet issue (install NLTK as --user but its impossible in virtualenv cause we are already in poetry)
- rm -rf /home/ren/nltk_data

2. Reinstall NLTK:

Sometimes, the issue could be with the installation of nltk. Reinstall it using Poetry:

bash

poetry run pip uninstall nltk
poetry run pip install nltk

3. Download WordNet Data Manually:

Instead of relying on nltk.download, let's manually download the wordnet data:

    Download the WordNet Corpus:

    Download the WordNet data manually from the NLTK GitHub repository:

wget https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip

Unzip the WordNet Corpus:

Extract it to your nltk_data directory:

bash

    mkdir -p /home/ren/nltk_data/corpora
    unzip wordnet.zip -d /home/ren/nltk_data/corpora/

4. Verify Installation:

Now, try running the Python shell again and verify that the wordnet data can be loaded:

bash

poetry run python

Then, in the Python shell:

python

import nltk
nltk.data.path.append('/home/ren/nltk_data')
from nltk.corpus import wordnet as wn
wn.synsets('dog')

-- PYDANTIC AND SPACY COMPATIBILITY ERROR
--> go again back at ojd_daps_skills 1.0.1

- 
