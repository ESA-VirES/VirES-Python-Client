Introduction to notebooks
=========================

Jupyter notebooks are a convenient tool for interactive data exploration, rapid prototyping, and producing reports. The Virtual Research Environment provides free JupyterLab instances with persistent storage where you can run notebooks working with Swarm data.



.. list-table:: Notebook repositories
   :header-rows: 1

   *  -  Name (GitHub Link)
      -  View (static/docs)
      -  Launch/interact
      -  Description
   *  -  `Swarm-DISC/Swarm_notebooks <https://github.com/Swarm-DISC/Swarm_notebooks>`_
      -  .. image:: https://img.shields.io/badge/render-JupyterBook-orange.svg
            :target: https://swarm.magneticearth.org
      -  .. image:: https://img.shields.io/badge/nbgitpuller-VRE-blue
            :target: https://vre.vires.services/hub/user-redirect/git-pull?repo=https://github.com/Swarm-DISC/Swarm_notebooks&urlpath=lab/tree/Swarm_notebooks/notebooks/
      -  Curated Swarm notebooks for scientists
   *  -  `pacesm/jupyter_notebooks <https://github.com/pacesm/jupyter_notebooks>`_
      -  .. image:: https://img.shields.io/badge/render-nbviewer-orange.svg
            :target: https://nbviewer.jupyter.org/github/pacesm/jupyter_notebooks
      -  .. image:: https://img.shields.io/badge/nbgitpuller-VRE-blue
            :target: https://vre.vires.services/hub/user-redirect/git-pull?repo=https://github.com/pacesm/jupyter_notebooks&urlpath=lab/tree/jupyter_notebooks/
      -  Reference mainly during new product registration and configuration


.. note::

  Sometimes notebooks won't render directly on the GitHub website (or are slow). Try `nbviewer <https://nbviewer.jupyter.org/>`_ instead (see the "Render" links above).
  
  In the case of ``Swarm_notebooks``, the notebooks are stored in the repository *without outputs included*, so are better viewed at `swarm.magneticearth.org <https://swarm.magneticearth.org>`_ (the *Jupyter Book* link above)

Notebooks can be uploaded to JupyterLab using the "Upload" button (which means you must first download the notebooks to your computer from GitHub). To easily access a full repository, open a Terminal and use git:

To clone a repository to your working space::

    git clone https://github.com/Swarm-DISC/Swarm_notebooks.git

(this will clone it into ``Swarm_notebooks`` within your current directory)

To clear any changes you made and fetch the latest version, from within ``Swarm_notebooks`` run::

    git fetch
    git reset --hard origin/master

The *nbgitpuller* links above perform a ``git clone`` operation for you, and applies updates when you re-click the link using special `automatic merging behaviour <https://jupyterhub.github.io/nbgitpuller/topic/automatic-merging.html>`_. Sometimes it may be necessary to perform the git operations directly instead.