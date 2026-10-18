"""文言の切り替え（de = 原文, en = 再構成, ja = 和訳）。

{endowment} {currency} {base} {fee} {rate} は session config から埋める。
{give} {keep} {bonus} {payout} は画面ごとに fill() で埋める。未知のキーはそのまま残す。
"""
from . import de, en, ja

_TEXTS = dict(de=de.TEXT, en=en.TEXT, ja=ja.TEXT)
SOURCES = dict(de=de.SOURCE, en=en.SOURCE, ja=ja.SOURCE)


class _Keep(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def fill(value, **kwargs):
    if isinstance(value, str):
        return value.format_map(_Keep(kwargs))
    if isinstance(value, dict):
        return {k: fill(v, **kwargs) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, **kwargs) for v in value]
    return value


def money(cfg, v):
    """原研究の表記に合わせる: ドイツ語は 10,70、英語は 10.70。"""
    s = f'{v:.2f}'
    if cfg['lang'] == 'de':
        s = s.replace('.', ',')
    return s


def texts(player):
    cfg = player.session.config
    lang = cfg['lang']
    fmt = dict(
        endowment=money(cfg, cfg['endowment']),
        currency=cfg['currency_label'],
        base=money(cfg, cfg['base_payout']),
        fee=money(cfg, cfg['flat_fee']),
        rate=f"{cfg['conversion_rate']:g}",
    )
    return fill(_TEXTS[lang], **fmt)
