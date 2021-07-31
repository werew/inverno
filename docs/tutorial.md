# Tutorial 🧑‍🏫

This tutorial walks you through creating and configuring a new Inverno portfolio from scratch.

## Installation ✨

If you haven't yet installed Inverno, follow the steps [here](https://github.com/werew/inverno/blob/main/docs/installation.md#installation-) to install it.

## Create a new project

After installing Inverno, you should have get a new command named `inverno`, try typing it in your terminal of choice:

```sh
$ inverno --help
Usage: inverno [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  gen-report   Generate an html report from a config
  new-project  Generate a template for a new project
```

At the time being Inverno offers two commands `gen-report` and `new-project`.
Let's use the latter to create a new blank portfolio:

```sh
$ mkdir myproject && inverno new-project myproject
```

This should have created a new blank project inside the folder `myproject`:

```sh
$ ls myproject
project.yml  transactions.csv
```

You should now see two files in there: 
 - `project.yml`: a project configuration template
 - `transactions.csv`: an example list of transactions

At the moment the project configuration consists only of a list of transactions (all the rest is commented out):

```yml
transactions:
  - format: standard           # Transactions format
    file: transactions.csv     # Transactions file
```

This tells Inverno to load the transactions in the `transactions.csv` file which contains some example of transactions. 
You can open and edit .csv files using any spreedsheet software such as Excel, Google Sheets, LibreOffice Calc, etc.

![https://imgur.com/UtBQ3Td.png](https://imgur.com/UtBQ3Td.png)

As you can see there are a couple of cash deposits and some purchases of Facebook, Google and Apple stock.

This is enough to generate our first report:

```sh
$ inverno gen-report myproject/project.yml myproject/report
```

Congrats :) you have just generated your first report in `myproject/report`:

```sh
$ ls myproject/report
css  index.html  js  media  node_modules  package.json  package-lock.json  vendor
```

To view it, simply open the `index.html` file using your browser of choice.
