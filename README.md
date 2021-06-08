# nb_autoimports

## Install

`$ pip install git+https://github.com/sshh12/nb_autoimports --upgrade`

## Usage

Load with `%load_ext nb_autoimports` and create a cell with just `# autoimport:`. It's best to keep this cell seperate from other code since it's contents will be overridden by this extension.

### Fix basic imports

_See [common_index.py](https://github.com/sshh12/nb_autoimports/blob/main/nb_autoimports/common_index.py) for built-in aliases._

![basic example](https://user-images.githubusercontent.com/6625384/120899493-a0c73000-c5f5-11eb-8888-7f7ecb3b8870.gif)

### Fix and rerun

![rerun example](https://user-images.githubusercontent.com/6625384/120899644-67db8b00-c5f6-11eb-9d23-1d65c93f13c8.gif)

### Import from custom modules

_Include import names as a comma separated list. The order listed will be used as the lookup order._

![custom example](https://user-images.githubusercontent.com/6625384/120899933-bb9aa400-c5f7-11eb-8aa5-6e5c6397e12c.gif)

## More built-in imports

Fill free to PR an update [common_index.py](https://github.com/sshh12/nb_autoimports/blob/main/nb_autoimports/common_index.py).
