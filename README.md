# cronos

Cronos is a exam rescheduling system and makeups+accommodations request portal. It was
originally created for MIT's course 6.1220: Design and Analysis of Algorithms.

![](https://scripts.mit.edu/media/powered_by.gif)

## Installation

It is non-trivial to deploy this to MIT's Scripts server, mainly because it has very
outdated software versions from the dinosaur ages. At time of writing, Django is
available only in Python2.7, and the latest Python3 version has a broken Pip
installation.

Below are step-by-step instructions for deploying Cronos to an Athena locker.

### Virtualenv setup

To get around this, install [Miniforge][miniforge] using the download script for x86
Linux.  Then:

1. Give Scripts access to your Miniforge installation.
   ```bash
   add consult
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

### Creating the scripts service

The instructions below are based on those given [here][quickstart].

```bash
add scripts
scripts
# Select Django when prompted and provide a reasonable admin account.
```

[quickstart]: <https://scripts.mit.edu/start/>

### Importing the Cronos project

The instructions below are based on those given [here][import].

1. Evict the contents of `/mit/lockername/Scripts/django/projname`. Replace it with a
   clone of this repository and then make sure Scripts has access to it:
   ```bash
   fsr sa -dir /mit/lockername/Scripts/django/projname -acl daemon.scripts write
   ```
1. In `manage.py` and `index.fcgi`, change the shebang to the `python` installed in your
   conda environment. For example, mine looks like this:
   ```python
   #!/afs/athena.mit.edu/user/j/e/jerrym/miniforge3/envs/cronos/bin/python
   ```
   Also update the lockername in `index.fcgi` to your own locker.
1. Copy `index.fcgi` to `/mit/lockername/web_scripts/projname/index.fcgi`.
1. Generate a production-secure `SECRET_KEY` and set `DEBUG` to `False` in
   `cronos/settings.py`. Also configure `ALLOWED_HOSTS` to be the domain of your locker.

[import]: <https://scripts.mit.edu/faq/127/how-can-i-import-an-outside-django-project>

### Setting up MySQL

1. Don't. I tried a lot and couldn't get it to work. I think the MySQL server provided
   by Scripts is a dinosaur. Just accept that you'll be serving a production system
   backed by SQLite.
1. You should still initialize your database though!
   ```bash
   ./manage.py migrate
   ```
