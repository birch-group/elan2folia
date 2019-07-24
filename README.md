# elan2folia

## How to create new stage-4 "mystemmed" files
This task is performed by running a Python script.

### Prerequisite
The Python environment needs to have the following third-party packages installed:
* [pymystem3](https://github.com/nlpub/pymystem3)
* [pympi-ling](https://github.com/dopefishh/pympi)
* [folia](https://github.com/proycon/foliapy)

### Assumption
The folder structure on your computer is the same as the folder structure on this GitHub page.

### Script execution
For example, to create a new stage-4 "mystemmed" file from _**B_2014_10_24_1.eaf**_:
* copy/paste _**B_2014_10_24_1.eaf**_ into "**data**" subfolder of "**elan2folia**" folder
* run the following command line under "**elan2folia**" folder:
  ```shell
  python elan2folia.py B_2014_10_24_1
  ```
* look for the output file, _**B_2014_10_24_1.folia.xml**_ , in "**data**" subfolder after the script has been executed

![python elan2folia B_2014_10_24_1](https://birch.flowlu.com/files/download/77718dcd-ad82-11e9-b3dc-fa163e7d9ee1)
