
# Tutorial 🧑‍🏫

This tutorial walks you through creating and configuring a new Inverno portfolio from scratch.

## Installation ✨

If you haven't yet installed Inverno, follow the steps [here](https://github.com/werew/inverno/blob/main/docs/installation.md#installation-) to install it.

## Creating a new project 📰

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

```sh
$ ls myproject/report
css  index.html  js  media  node_modules  package.json  package-lock.json  vendor
```

To view it, simply open the `index.html` file using your browser of choice.
You should see something like this:

<img src="https://user-images.githubusercontent.com/10875013/127753180-71dc4f64-decb-4caf-98fa-86606ddd226b.png" alt="drawing" width="40%"/>


## Configuring Transactions 💸

As we saw in the previous section, the project configuration needs a list of transactions.
Transactions are listed in a separate .csv file, which is specified in the config as follows:

```yml
transactions:
  - format: standard           # Transactions format
    file: transactions.csv     # Transactions file
```

CSV files can be edited using any spreadsheet software (e.g. Excel).
You can provide as many transactions files as you want:

```yml
transactions:
  - format: standard
    file: transactions1.csv
  - format: schwab
    file: transactions2.csv
```

The `format` field specifies which format the transaction file is using. 
At the moment the available formats are `standard` and `schwab`. 

The `schwab` format is compatible with the list of transactions exportable from [Charles Schwab](https://schwab.com/) brokerage platform.

If you are manually filling in your transactions you should use the `standard` format.
In this format, each row corresponds to a transaction.

Your transactions file will have the following columns:

- **date**: day the transaction happened (e.g. 10/02/21)
- **action**: type of transaction, available types are:
  - ***buy***: for purchases of new holdings (e.g. buying stock)
  - ***sell***: for selling holdings (e.g. selling stock)
  - ***cash_in***: for cash flowing in (e.g. cash deposit, salary, etc.) 
  - ***cash_out***: for cash flowing out (e.g. withdrowal)
  - ***tax***: for any sort of tax payment associated to the investment account
  - ***vest***: for [vesting](https://www.investopedia.com/terms/v/vesting.asp) events (e.g. from [RSU](https://www.investopedia.com/terms/r/restricted-stock-unit.asp)) 
  - ***dividends***: for dividends payed by an holding
  - ***split***: for [stock split](https://www.investopedia.com/terms/s/stocksplit.asp) events
- **name**: (optional) name of the holding, can be anything (e.g. Google, Facebook, MyFund, etc.)
- **ticker**: (optional) ticker of the holding, if applicable (e.g. GOOGL, FB, etc.)
- **isin**: (optional) [ISIN](https://www.investopedia.com/terms/i/isin.asp) of the holding, if applicable (e.g. US38259P7069)
- **quantity**: (needed for buy/sell/vest transactions) number of holdings purchased/sold/vested (e.g. 3.5)
- **price**: (either price or amount are needed for buy/sell transactions) holding price at the moment of the purchase/sale, corresponds to the price multiplied by the quantity (e.g. $102.2)
- **amount**: (either price or amount are needed for buy/sell transactions) total cash amount of the transaction price at the moment of the purchase/sale, corresponds to the price multiplied by the quantity (e.g. $424.2)
- **fees**: (optional) transaction costs (e.g. $2.4)

Once again, here is an example of transactions:
![https://imgur.com/UtBQ3Td.png](https://imgur.com/UtBQ3Td.png)

## Configuring Prices

## Configuring Options

## Adding Metadata
