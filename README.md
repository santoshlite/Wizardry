
# Wizardry, the Algorithmic Wizard 💫

Wizardry is an open-source **framework** and **CLI** built on the top of [**lean cli**](https://github.com/QuantConnect/lean-cli) for **building powerful algorithmic trading strategies faster** and **easier** (for Lean/QuantConnect)

<div align="center">
<img src="https://raw.githubusercontent.com/ssantoshp/Wizardry/main/documentation/wiz.png"/>

![](https://img.shields.io/badge/build-passing-orange)
![](https://static.pepy.tech/personalized-badge/wizardry?period=total&units=international_system&left_color=black&right_color=brightgreen&left_text=Users)
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

Before going into details for each of these commands, **click on the image below to see a demo/tutorial of Wizardry**

[<img src="https://i.ibb.co/R71vr7k/pic.png" width="200"/>](https://www.youtube.com/watch?v=1ejiNJUeID4)

So, let's get into these commands

### wizardry create ProjectName

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

Note: For every other commands, you'll need to be in your project directory in order to make it work.

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

## Contribution 

If you have some suggestions or improvements don't hesitate to create an issue or make a pull request. Any help is welcome!

Just make sure you respect that 
```
When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.
```

