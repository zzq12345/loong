import json
from urllib.parse import urlparse, parse_qs

from utils import my_requester, encrypt_data, decrypt_data


def get_channel(channel_id):
    channel_info = {
        'id': channel_id,
    }
    get_channel_api = f'https://api2.4gtv.tv/Channel/GetChannel/{channel_id}'
    headers = {
        'User-Agent': 'okhttp/3.12.11'
    }
    response = my_requester('GET', url=get_channel_api, headers=headers)
    if not response:
        print('Failed to get channel info')
        return channel_info

    response_dict = response.json()
    channel_info['name'] = response_dict['Data']['fsNAME']
    request_dict = {
        'fnCHANNEL_ID': response_dict['Data']['fnID'],
        'fsASSET_ID': response_dict['Data']['fs4GTV_ID'],
        'fsDEVICE_TYPE': 'mobile',
        'clsIDENTITY_VALIDATE_ARUS': {'fsVALUE': ''}
    }
    encrypt = encrypt_data(json.dumps(request_dict))
    request_data = {'value': encrypt.decode()}
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    response = my_requester('POST',
                            url='https://api2.4gtv.tv/Channel/GetChannelUrl3',
                            data=request_data, headers=headers)
    if not response:
        print('Failed to get channel play info')
        return channel_info

    response_dict = response.json()
    if 'Data' not in response_dict:
        print('Failed to get channel play info')
        return channel_info

    decrypt = decrypt_data(response_dict['Data'])
    playlist = json.loads(decrypt)
    play_url = playlist['flstURLs'][0]
    if play_url.startswith('https://4gtvfree-cds.cdn.hinet.net'):
        play_url = play_url.replace('/index.m3u8?', '/1080.m3u8?')
    else:
        play_url = get_play_raw(play_url, return_type='url')

    channel_info['play_url'] = play_url
    return channel_info


def get_play_raw(url, return_type='raw'):
    headers = {
        'User-Agent': 'okhttp/3.12.11'
    }
    response = my_requester('GET', url=url, headers=headers)
    parsed_url = urlparse(url)
    if not response:
        return None

    resp_text = response.text.strip()
    latest_line = resp_text.split('\n')[-1]
    url_path = '/'.join(parsed_url.path.split('/')[0:-1])
    new_url = f'{parsed_url.scheme}://{parsed_url.netloc}{url_path}/{latest_line}'

    if return_type == 'url':
        return new_url

    if '.ts' in latest_line:
        return resp_text
    else:
        return get_play_raw(new_url, return_type)


def play_4gtv(play_url):
    m3u8_raw = get_play_raw(play_url)
    if not m3u8_raw:
        print('Failed to get play url')

    if play_url.startswith('https://4gtvfree-cds.cdn.hinet.net'):
        # live 格式的处理
        base_url = play_url.split('?')[0].rsplit('/', 1)[0]
        lines = []
        for line in m3u8_raw.split('\n'):
            if line.startswith('#EX') or not line.strip():
                lines.append(line)
            elif '.ts' in line:
                ts_file = line.split('?')[0]
                parsed_url = urlparse(line)
                params = parse_qs(parsed_url.query)
                params_simplified = {k: v[0] for k, v in params.items()}

                ts_url = (f'{base_url}/{ts_file}?'
                          f'token1={params_simplified["token1"]}'
                          f'&expires1={params_simplified["expires1"]}')
                lines.append(ts_url)
            else:
                lines.append(line)
        m3u8_raw = '\n'.join(lines)

    else:
        channel = play_url.split('?')[0].split('/')[-3]
        lines = []
        prex = f'https://litvpc-hichannel.cdn.hinet.net/live/pool/{channel}/litv-pc/'
        for line in m3u8_raw.split('\n'):
            if line.startswith('#EXT') or not line.strip():
                lines.append(line)
            else:
                ts_file = line.split('?')[0]
                ts_file = ts_file.replace('video=2000000', 'video=6000000')
                ts_file = ts_file.replace('video=2936000', 'video=5936000')
                ts_file = ts_file.replace('video=3000000', 'video=6000000')
                ts_file = ts_file.replace('avc1_2000000=3', 'avc1_6000000=1')
                ts_file = ts_file.replace('avc1_2000000=6', 'avc1_6000000=1')
                ts_file = ts_file.replace('avc1_2936000=4', 'avc1_6000000=5')
                ts_file = ts_file.replace('avc1_3000000=3', 'avc1_6000000=1')
                ts_url = f'{prex}{ts_file}'
                lines.append(ts_url)

        m3u8_raw = '\n'.join(lines)
    print(m3u8_raw)


if __name__ == '__main__':
    info = get_channel('1')
    print(info)
    if 'play_url' in info:
        play_4gtv(info['play_url'])
