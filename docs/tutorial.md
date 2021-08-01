
# Tutorial 🧑‍🏫

This tutorial walks you through creating and configuring a new Inverno portfolio from scratch.

**Index**
- [Installation](https://github.com/werew/inverno/blob/main/docs/tutorial.md#installation-)
- [Creating a new project](https://github.com/werew/inverno/blob/main/docs/tutorial.md#creating-a-new-project-)
- [Configuring transactions](https://github.com/werew/inverno/blob/main/docs/tutorial.md#configuring-transactions-)
- [Configuring prices](https://github.com/werew/inverno/blob/main/docs/tutorial.md#configuring-prices-)
- [Configuring options](https://github.com/werew/inverno/blob/main/docs/tutorial.md#configuring-options-%EF%B8%8F)
- [Adding metadata](https://github.com/werew/inverno/blob/main/docs/tutorial.md#adding-metadata-)
   - [Multiple values](https://github.com/werew/inverno/blob/main/docs/tutorial.md#multiple-values)
   - [Nested metadata](https://github.com/werew/inverno/blob/main/docs/tutorial.md#nested-metadata)

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

<img src="https://user-images.githubusercontent.com/10875013/127753180-71dc4f64-decb-4caf-98fa-86606ddd226b.png" alt="drawing" width="50%"/>


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
  - *buy*: for purchases of new holdings (e.g. buying stock)
  - *sell*: for selling holdings (e.g. selling stock)
  - *cash_in*: for cash flowing in (e.g. cash deposit, salary, etc.) 
  - *cash_out*: for cash flowing out (e.g. withdrowal)
  - *tax*: for any sort of tax payment associated to the investment account
  - *vest*: for [vesting](https://www.investopedia.com/terms/v/vesting.asp) events (e.g. from [RSU](https://www.investopedia.com/terms/r/restricted-stock-unit.asp)) 
  - *dividends*: for dividends payed by an holding
  - *split*: for [stock split](https://www.investopedia.com/terms/s/stocksplit.asp) events
- **name**: (optional) name of the holding, can be anything (e.g. Google, Facebook, MyFund, etc.)
- **ticker**: (optional) ticker of the holding, if applicable (e.g. GOOGL, FB, etc.)
- **isin**: (optional) [ISIN](https://www.investopedia.com/terms/i/isin.asp) of the holding, if applicable (e.g. US38259P7069)
- **quantity**: (needed for buy/sell/vest transactions) number of holdings purchased/sold/vested (e.g. 3.5)
- **price**: (either price or amount are needed for buy/sell transactions) holding price at the moment of the purchase/sale, corresponds to the price multiplied by the quantity (e.g. $102.2)
- **amount**: (either price or amount are needed for buy/sell transactions) total cash amount of the transaction price at the moment of the purchase/sale, corresponds to the price multiplied by the quantity (e.g. $424.2)
- **fees**: (optional) transaction costs (e.g. $2.4)

Once again, here is an example of transactions: 

![https://imgur.com/UtBQ3Td.png](https://imgur.com/UtBQ3Td.png)

## Configuring Prices 💰

Inverno will try to fetch prices from Yahoo Finance. If prices of an holding are not available on Yahoo Finance, Inverno will try to estimate them based on the transactions (by interpolating the prices you have provided in the transactions). 
This last method isn't very precise (and might not be possible if there are too few transactions). In such cases you might want to provide the prices on your own. 

You can specify a prices file for one or more holdings as follows: 

```yml
prices:
    - match:
        name: My Fund
      file: my_fund_prices.csv
    - match:
        ticker: FB
      file: fb_prices.csv
```

The `match` section lets you specify the holding by name, ticker or ISIN.

Prices must be provided as CSV files with ***date*** and ***price*** columns, where each row represents the price for that day:

[![https://imgur.com/CPMov9k.png](https://imgur.com/CPMov9k.png)](https://imgur.com/CPMov9k.png)


## Configuring Options ☑️

You can add an `options` section to your project to specify extra config parameter:

```yml
options:
  title: My Portfolio        # Name of the project
  days: 90                   # Show last N days (default is 90, relative to end_date)
  end_date: 25/04/21         # Do not show after this date (defaults to today)
  currency: USD              # Convert everything to this currency (default USD)
```



## Adding Metadata 📊

Peraphs one of the coolest features of Inverno is the ability to associate metadata to any holding.
This is done via the `meta` section.

Each metadata entry consists of a `match` section (similar to the one used for prices) which can match an holding by its name, ticker or ISIN,
and an `apply` section containing a list of attributes and values. Let's look at an example:

```yml
meta:
  - match:
      ticker: FB                       # Match holding by its ticker
    apply:
      sector: Communication Services   # Set attribute "sector" to "Communication Services"
```

Here we are saying that the *sector* of our holding with ticker FB is "Communication Services".
Notice that instead of *sector* **we could have put anything!**

Let's add another holding:


```yml
meta:
  - match:
      ticker: FB
    apply:
      sector: Communication Services
  - match:
      ticker: JNJ
    apply:
      sector: Health Care
```

As a result we will get a new *sector* section in our report, showing how our holdings are distrubuted with respect to the sectors and how each sector is performing: 

![Inverno Report Sector Section Screenshot](https://user-images.githubusercontent.com/10875013/127777754-05c80534-94e0-46d9-a376-e87f3e6ff64c.png)

Notice that holdings for which we haven't specified any sector are left as "unkown". 
Using the same technique we could specify attributes for anything of interest: company cap, ratings, location, etc.

### Multiple values

Sometime an holding may extend over multiple sectors, this is common for mutual funds, ETFs, etc. 
Inverno let's you specify multiple values for an attribute: 

```yml
meta:
  - match:
      name: My Fund
    apply:
      sector:
          Information Technology: 50%
          Communication Services: 30%
```

Here we are saying that the sector of *My Fund* is 50% *Information Technology*, 30% *Communication Services* and 20% unknown.


### Nested metadata

Some holdings are simply the composition of other holdings. 
Let's take an actual example: [Vanguard's Lifestrategy](https://investor.vanguard.com/mutual-funds/lifestrategy/#/) funds are nothing but a composition of multiple other Vanguard funds. 

This relation can be specified using the `composition` meta section:


```yml
  - match:
      name: LifeStrategy® 80% Equity Fund - Accumulation
    apply:
      type:
        equity: 80%
        bonds: 20%
    composition:
      name:
        U.S. Equity Index Fund GBP Acc:  19.37%
        FTSE U.K. All Share Index Unit Trust GBP Acc:  19.27%
        FTSE Developed World ex-U.K. Equity Index Fund GBP Acc:  19.26%
        Global Bond Index Fund GBP Hedged Acc: 14.01%
        Emerging Markets Stock Index Fund - Accumulation: 6.96%
        FTSE Developed Europe ex-U.K. Equity Index Fund GBP Acc: 5.42%
        S&P 500 UCITS ETF (USD) Accumulating:  4.61%
        Japan Stock Index Fund GBP Acc:  2.80%
        U.K. Government Bond Index Fund GBP Acc: 2.49%
        U.K. Inflation-Linked Gilt Index Fund GBP Acc: 1.89%
        U.K. Investment Grade Bond Index Fund GBP Acc: 1.60%
        Pacific ex-Japan Stock Index Fund GBP Acc: 1.46%
        FTSE 100 UCITS ETF (GBP) Distributing: 0.79%
        FTSE 250 UCITS ETF (GBP) Distributing: 0.07%
        U.K. Gilt UCITS ETF (GBP) Distributing:  0.01%
```

Here we are saying that the fund named *LifeStrategy® 80% Equity Fund - Accumulation* is composed of all those funds in the measure specified by the percentages. 
In this case composing holding are specified by name, it is also possible to specify them by ticker or ISIN:

```yml
  - match:
      name: My Fund
    apply:
      type: equity
    composition:
      ticker:
         FB: 10%
```
      
If you specify an attribute in the `apply` section, this will have priority over the `composition`. This means that, in the example above, the type of *My Fund* will be always 100% equity regardless of the type of its sub-holdings.

