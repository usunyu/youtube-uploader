# youtube-uploader
Auto fill video info data and upload to YouTube

### Quick Start

```
$ python youtube_uploader.py yportmaster video.mp4 https://www.bilibili.com/video/av38604809 "《哥谭》第二季"
```

### Add Alert

Pop alert box when complete, append commend below:
```
&& osascript -e 'tell application (path to frontmost application as text) to display dialog "The script has completed" buttons {"OK"} with icon caution'
```
