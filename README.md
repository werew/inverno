# Inverno 📈

Inverno is a flexible investments portfolio tracker.


## How it works ⁉️

Inverno takes a config file as input and generates an html report. You provide information about transactions, Inverno takes care of the rest. 

See an example report [here](https://ret2libc.com/static/inverno_report/).

<img src="https://user-images.githubusercontent.com/10875013/124403088-68b62880-dd2c-11eb-8332-7dfd50c710ba.png" alt="drawing" width="40%"/>

## Try it now 🔥

Install Inverno from PyPi:
```sh
pip install inverno
```

Create a new project:
```sh
mkdir myproject && inverno new-project myproject
```

Generate a report:
```sh
inverno gen-report myproject/project.yml myproject/report
```

Check the [tutorial](https://github.com/werew/inverno/blob/main/docs/tutorial.md#tutorial-) to know more!


## Documentation 📚

- [Installation](https://github.com/werew/inverno/blob/main/docs/installation.md#installation-)
- [Tutorial](https://github.com/werew/inverno/blob/main/docs/tutorial.md#tutorial-)
