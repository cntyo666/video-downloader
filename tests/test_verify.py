import requests

resp = requests.get('http://127.0.0.1:5000/')
html = resp.text

checks = {
    'Header title': '视频下载器' in html,
    'Platform tags': '回森' in html and '抖音' in html and '快手' in html,
    'Tab switching': 'data-tab' in html,
    'Single panel': 'panel-single' in html,
    'Batch panel': 'panel-batch' in html,
    'Parse button': 'btn-parse' in html,
    'Download func': 'doDownload' in html,
    'CDN direct logic': 'direct_url' in html,
    'Toast system': 'toast' in html,
    'Dark theme': '--bg:#0a0a0f' in html,
    'Responsive': 'max-width:640px' in html,
    'Cover image': 'result-cover' in html,
    'Spinner': 'spinner' in html or 'spin' in html,
    'Enter key': 'keydown' in html,
    'Error display': 'result-error' in html,
    'Batch API': 'batch_parse' in html,
}

print('UI Element Verification:')
all_ok = True
for name, ok in checks.items():
    symbol = 'PASS' if ok else 'FAIL'
    if not ok:
        all_ok = False
    print(f'  [{symbol}] {name}')

print(f'\nResult: {"ALL PASS" if all_ok else "SOME FAILED"}')
print(f'HTML size: {len(html)} bytes')
