Introduction to notebooks
=========================

Jupyter notebooks are a convenient tool for interactive data exploration, rapid prototyping, and producing reports. The Virtual Research Environment provides free JupyterLab instances with persistent storage where you can run notebooks working with Swarm data. For more information, see the `Swarm-VRE docs <https://swarm-vre.readthedocs.io/>`_.



.. list-table:: Notebook repositories
   :header-rows: 1
   :widths: 7 5 5

   *  -  Name (GitHub Link)
      -  View (nbviewer)
      -  Launch/interact (VRE)
   *  -  `Swarm-DISC/Swarm_notebooks <https://github.com/Swarm-DISC/Swarm_notebooks>`_
      -  .. image:: https://img.shields.io/badge/render-nbviewer-orange.svg
            :target: https://nbviewer.jupyter.org/github/Swarm-DISC/Swarm_notebooks
      -  (to do)
   *  -  `smithara/viresclient_examples <https://github.com/smithara/viresclient_examples>`_
      -  .. image:: https://img.shields.io/badge/render-nbviewer-orange.svg
            :target: https://nbviewer.jupyter.org/github/smithara/viresclient_examples
      -  (to do)
   *  -  `pacesm/jupyter_notebooks <https://github.com/pacesm/jupyter_notebooks>`_
      -  .. image:: https://img.shields.io/badge/render-nbviewer-orange.svg
            :target: https://nbviewer.jupyter.org/github/pacesm/jupyter_notebooks
      -  (to do)


.. note::

  Sometimes notebooks won't render directly on the GitHub website (or are slow). Try `nbviewer <https://nbviewer.jupyter.org/>`_ instead (see the "Render" links above).

Notebooks can be uploaded to JupyterLab using the "Upload" button (which means you must first download the notebooks to your computer from GitHub). To easily access a full repository, open a command line console and use git:

To clone a repository to your working space::

    git clone https://github.com/Swarm-DISC/Swarm_notebooks.git

(this will clone it into ``Swarm_notebooks`` within your current directory)

To clear any changes you made and fetch the latest version, from within ``Swarm_notebooks`` run::

    git fetch
    git reset --hard origin/master
