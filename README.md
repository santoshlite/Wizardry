
# Wizardry, the Algorithmic Wizard 💫

Wizardry is an open-source **CLI** built on the top of [**lean cli**](https://github.com/QuantConnect/lean-cli) for **building powerful algorithmic trading strategies faster** and **easier** (for Lean/QuantConnect)

<div align="center">
<img src="https://raw.githubusercontent.com/ssantoshp/Wizardry/main/documentation/wiz.png"/>

![](https://img.shields.io/badge/build-passing-orange)
![](https://img.shields.io/badge/Download-1.5k-brightgreen)
![](https://img.shields.io/badge/license-MIT-blue)
![](https://img.shields.io/badge/swag%20level-A++-yellow)
![](https://img.shields.io/badge/language-python🐍-blue)
![](https://camo.githubusercontent.com/97d4586afa582b2dcec2fa8ed7c84d02977a21c2dd1578ade6d48ed82296eb10/68747470733a2f2f6261646765732e66726170736f66742e636f6d2f6f732f76312f6f70656e2d736f757263652e7376673f763d313033)

</div>


## Installation 🧙

```python
pip install wizardry
```

## Usage 🏦

There are 6 commands in Wizardry CLI:

- ```wizardry create ProjectName``` **create a project** on which you can work on. You should alway start with this command when creating a new algorithm.

- ```wizardry framework``` enables user to define an **alpha**, a **universe**, a **portfolio construction** and a **risk managment model** to build the body of your strategy

- ```wizardry library``` enables user to **explore** and **"fork"** to their local machine about **100 algo trading strategies** from this [webpage](https://www.quantconnect.com/tutorials/strategy-library/strategy-library)

- ```wizardry backtest``` **backtest** your trading strategy on QuantConnect's cloud

- ```wizardry live``` deploy your algorithm **in live** with QuantConnect

- ```wizardry live``` **optimize your strategy** with QuantConnect


## Descriptions of these commands


### wizardry create ProjectName

![](https://raw.githubusercontent.com/ssantoshp/Wizardry/main/documentation/realone.gif)


This command allow you to create a project folder:
```
├── ProjectName
│   ├── .idea
│   │   ├── misc.xml
│   │   ├── modules.xml
│   │   ├── ProjectName.iml
│   │   └── workspace.xml
│   │   
│   ├── .vscode
│   │   ├── launch.json
|   |   └── settings.json
|   |  
│   ├── config.json
│   ├── main.py (where your algo is)
│   └── research.ipynb

```

Once you created the project, in order to work on it with wizardry, you'll need to go your project directory

```
cd ProjectName
```

**Note: For every other commands, you'll need to be in your project directory in order to make it work.**

### wizardry framework

![](https://raw.githubusercontent.com/ssantoshp/Wizardry/main/documentation/frame.gif)

It follows the same process than Quantconnect (+few extra features) :

- 🍈 **Universe Selection :** Select your assets
- 🍓 **Alpha Creation :** Generate trading signals
- 🍇 **Portfolio Construction :** Determine position size targets
- 🍉 **Execution :** Place trades to reach your position sizes
- 🍌 **Risk Management :** Manage the market risks

<div align="center">
<img src="https://cdn.quantconnect.com/web/i/docs/algorithm-framework/algorithm-framework.png"/>
</div>

### wizardry library

![](https://raw.githubusercontent.com/ssantoshp/Wizardry/main/documentation/lib1.gif)

### wizardry backtest

Run ```wizardry backtest``` in your project directory

What it will do:
- Push the local changes to the cloud
- Backtest in the cloud (with QuantConnect's data)
- Show you the result in your terminal
- Open a page with the backtesting's results

### wizardry optimize

Run ```wizardry optimize``` in your project directory

It will push the modifications to the cloud and offer different options in order to optimize your strategy.

Based on QuantConnect's ```lean cloud optimize``` command, check what it can do [here](https://www.quantconnect.com/docs/v2/lean-cli/tutorials/optimization/cloud-optimizations)


### wizardry live

Run ```wizardry live``` in your project directory

It will push the modifications to the cloud and deploy your strategy live.

Based on QuantConnect's ```lean cloud live``` command, check what it can do [here](https://www.quantconnect.com/docs/v2/lean-cli/tutorials/live-trading/cloud-live-trading)


## Issues and Feature Requests ##

Please submit bugs and feature requests as an issue. Before submitting an issue please read others to ensure it is not a duplicate.

## Contributors and Pull Requests ##

Contributions are warmly very welcomed but we ask you to read the existing code to see how it is formatted, commented and ensure contributions match the existing style. All code submissions must include accompanying tests. Please see the [contributor guide lines](contributor.md).

