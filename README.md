#  Wisdom Tree Online Course Bot

## About This

基于 Python selenium 的智慧树刷课 bot

## Feature

- 模拟用户在网页中的鼠标移动、点击等行为，不涉及对任何页面元素的篡改，相比很多常见的 js 脚本更为安全
- 使用 [undetected_chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) 作为浏览器驱动，使 bot 更难以被检测
- 能够检测并解决掉视频播放过程中的弹窗和弹题
- 能够检测视频的意外暂停并及时重新播放
- 能够自动播放下一个未完成任务点的视频
- 支持定时关闭功能
- 支持后台运行
- 当视频在较长时间内都无法正常播放时，bot 会直接终止，不会无期限的等待。这种情况常源于验证码弹窗。

## Requisite

- 环境：Python3

  注：Windows用户可直接在微软商店里面安装，无需配置权限和环境变量。

- 包管理器：pip

  Windows用户的安装可参考：https://phoenixnap.com/kb/install-pip-windows

- 所需的包：selenium, webdriver-manager

  可使用 pip 安装，命令：

  ```
  pip install selenium webdriver-manager undetected-chromedriver
  ```

- 其他：Chrome，以及一个拥有正常分辨率的系统

## Quick Start

直接执行脚本即可，您既可以使用命令行：

```bash
python3 bot.py
```

也可以使用支持 Python 的 IDE 来运行。

如要使用定时功能，使用命令行时附上参数即可。描述时间既可以使用时、分、秒（用冒号间隔），也可以直接以秒为单位

以定时30分钟为例：

```python
python3 bot.py 30:00
```

或者：

```python
python3 bot.py 1800
```

## Usage

使用前请先确保自己的系统分辨率是默认状态，否则会影响 bot 对网页元素的定位。

初次使用时浏览器会自动跳转到智慧树的登录界面，正常登录即可。登录后需要手动进入课程对应的视频页面，然后等待视频自动播放。注意从成功进入视频网页后到视频开始播放前**请不要**移动鼠标，否则有可能会干扰 bot 对鼠标的模拟，导致视频无法正常播放。

当视频开始播放后，即可将窗口最小化（如果您没有在右上角找到 `-`，可以先右键窗口然后再选择最小化）。此外，您还可以用其他窗口覆盖该窗口，或者关闭计算机的屏幕。这些都不会影响脚本的执行。

但遗憾的是，您不能更改窗口的大小，或者对页面进行缩放，否则也会影响 bot 对元素的定位。

需要注意的是，浏览器每次启动后都会在一个 Error Page 滞留五秒，如果没有检测到 url 的变更，则会直接使用上次储存的 url。因此，如果需要播放其他的课程，直接在浏览器启动后的五秒内输入相应的 url 即可，或者先输入智慧树的主页地址，然后手动进入视频页面。

由于 bot 储存了视频页面的 url 和 cookies，在二者有效期内，用户不必在每次启动脚本后手动输入 url 或重新登录。但如果页面要求登录，说明 cookies 已经失效，需要重新登录。如页面访问发生错误，说明 url 已失效，需要向浏览器输入正确的 url。同样，您也可以先打开智慧树的主页，然后手动进入视频页面。

## Issues

- 无法解决 Captcha 验证码弹窗
