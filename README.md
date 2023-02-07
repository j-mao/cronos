# cronos

Cronos is a exam rescheduling system and makeups+accommodations request portal. It was
originally created for MIT's course 6.1220: Design and Analysis of Algorithms.

## Installation

It is non-trivial to deploy this to MIT's Scripts server, mainly because it has very
outdated software versions from the dinosaur ages. At time of writing, Django is
available only in Python2.7, and the latest Python3 version has a broken Pip
installation.

While many of the below steps will work, you are on your own with figuring out the
details. Cronos is currently deployed at CSAIL instead.

### Virtualenv setup

Install [Miniforge][miniforge] using the download script for x86 Linux. Then:

1. Give Scripts access to your Miniforge installation.
   ```bash
   fsr sa -dir /path/to/miniforge3 -acl daemon.scripts write
   ```
1. Install dependencies into a conda virtualenv.
   ```bash
   conda env create -f environment.yml
   ```
1. Figure out where your custom Python installation lives. You'll need it later.
   ```bash
   conda activate cronos
   which python
   ```

[miniforge]: <https://github.com/conda-forge/miniforge>

### Importing the Cronos project

1. Clone Cronos into your locker at a web-accessible subdirectory.
1. In `manage.py` and `index.fcgi`, change the shebang to the `python` installed in your
   conda environment. For example, mine looks like this:
   ```python
   #!/afs/csail.mit.edu/proj/courses/6.046/miniforge3/envs/cronos/bin/python
   ```
1. In `cronos/settings.py`, configure a production-secure `SECRET_KEY`, set `DEBUG` to
   `False`, set `ALLOWED_HOSTS`.

### Setting up MySQL

1. Create a database at [CSAIL MySQL](mysql.csail.mit.edu).
1. Configure `DATABASES` in `cronossettings.py` to point to it.
1. Initialize your database!
   ```bash
   ./manage.py migrate
   ```

### Setting up OIDC

1. Register a client at the [MIT OIDC Pilot](oidc.mit.edu).
1. Configure `AUTHLIB_OAUTH_CLIENTS` to point to it.

### Caveat

Authlib assumes that JWS specifies `kid`, but it [doesn't actually have to][oidc-kid].
This causes some HTTP 500s. To fix this, find `sync_openid.py` in your conda
environment, and make the following change:
```diff
40c40
<                 return jwk_set.find_by_kid(header.get('kid'))
---
>                 return jwk_set.find_by_kid(header.get('kid', 'rsa1'))
44c44
<                 return jwk_set.find_by_kid(header.get('kid'))
---
>                 return jwk_set.find_by_kid(header.get('kid', 'rsa1'))
```

[oidc-kid]: https://github.com/lepture/authlib/issues/462
