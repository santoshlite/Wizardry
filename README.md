# Wizardry, the Algorithmic Wizard 💫

Wizardry is a **CLI** for **building powerful algorithmic trading strategies faster** and **easier** (for Lean/QuantConnect)

## Installation 🧙

```
pip install wizardry
```

## Usage 🏦

There is 3 commands in Wizardry CLI:

- ```wizardry framework``` enables user to define an **alpha**, an **universe**, a **portfolio construction** and a **risk managment model** to build the body of your strategy

- ```wizardry library``` enables user to **explore** and **"fork"** to their local machine about **100 algo trading strategies** from this [webpage](https://www.quantconnect.com/tutorials/strategy-library/strategy-library)

- ```wizardry backtest``` Backtesting is not available for the moment but this command line will guide you on **how to backtest your code to Quantconnect!**

Before going into details for each of these commands, **click on the image below to see a demo/tutorial of Wizardry**

[<img src="https://i.ibb.co/R71vr7k/pic.png" width="200"/>](https://www.youtube.com/watch?v=1ejiNJUeID4)

So, let's get into these 3 commands

### wizardry framework

![](https://raw.githubusercontent.com/ssantoshp/Wizardry/main/documentation/frame.gif)

It follows the same process than Quantconnect (+few extra features) :

- **Universe Selection :** Select your assets
- **Alpha Creation :** Generate trading signals
- **Portfolio Construction :** Determine position size targets
- **Execution :** Place trades to reach your position sizes
- **Risk Management :** Manage the market risks

### wizardry library

![](https://raw.githubusercontent.com/ssantoshp/Wizardry/main/documentation/lib1.gif)

### wizardry backtest

Here is how I advise you to backtest your strategy made on Wizardry :

For the first time:

1. run ```pip install lean``` in an empty folder

2. run ```lean login``` in this same directory with the command prompt and give your QuantConnect ID and API token (you can get them [here](https://www.quantconnect.com/settings/))

3. run ```lean create-project "Project Name"``` in the same directory with your command prompt

4. Replace the ```main.py``` file in the "Project Name" folder by your ```main.py```

5. run ```lean cloud push --project "Project Name"```

6. finally, run ```lean cloud backtest "Project Name" --open --push'``` (just repeat this command when modifying the file)

You're done!🚀

If you want to watch a tutorial about to make that, you can watch my video from [here](https://youtu.be/1ejiNJUeID4?t=189)

## Credit
Made possible thanks to QuantConnect

## Contribution 

If you have some suggestions or improvements don't hesitate to create an issue or make a pull request. Any help is welcome!

Just make sure you respect that 
```
When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.
```

