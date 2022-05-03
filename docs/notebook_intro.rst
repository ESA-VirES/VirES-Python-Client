Introduction to notebooks
=========================

Jupyter notebooks are a convenient tool for interactive data exploration, rapid prototyping, and producing reports. The Virtual Research Environment (VRE) provides free JupyterLab instances with persistent storage where you can run notebooks.

The VRE is a whole analysis suite, including many other libraries from the Python ecosystem. We provide recipes in the form of noteboooks compiled into a "Jupyter Book" to show how viresclient can be blended together with other libraries to access, visualise, and analyse data.

.. list-table:: Notebook repositories
   :header-rows: 1

   *  -  Name / GitHub
      -  View
      -  Interact
   *  -  `Swarm-DISC/Swarm_notebooks <https://github.com/Swarm-DISC/Swarm_notebooks>`_
      -  .. image:: https://jupyterbook.org/badge.svg
            :target: https://notebooks.vires.services
      -  .. image:: https://img.shields.io/badge/nbgitpuller-VRE--Swarm-blue
            :target: https://vre.vires.services/hub/user-redirect/git-pull?repo=https://github.com/Swarm-DISC/Swarm_notebooks&urlpath=lab/tree/Swarm_notebooks/notebooks/
   *  -  `ESA-VirES/Aeolus-notebooks <https://github.com/ESA-VirES/Aeolus-notebooks>`_
      -  .. image:: https://jupyterbook.org/badge.svg
            :target: https://notebooks.aeolus.services
      -  .. image:: https://img.shields.io/badge/nbgitpuller-VRE--Aeolus-blue
            :target: https://vre.aeolus.services/hub/user-redirect/git-pull?repo=https://github.com/ESA-VirES/Aeolus-notebooks&urlpath=lab/tree/Aeolus-notebooks/notebooks&branch=main

.. note::

      The *nbgitpuller* links above perform *git* operations for you, applying updates when you re-click the link using special `automatic merging behaviour <https://jupyterhub.github.io/nbgitpuller/topic/automatic-merging.html>`_. Sometimes it may be necessary to perform the git operations directly instead.

      To clear any changes you made and fetch the latest version, from within ``Swarm_notebooks`` or ``Aeolus-notebooks`` run from a terminal::

            git fetch
            git reset --hard origin/master
