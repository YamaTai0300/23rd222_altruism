"""表示文言の切り替え。

texts(player) は player.lang（'ja' / 'en'）に応じた辞書を返す。
文字列中の {endowment} {currency} {fee} {check_amount} {step} は session config の値で埋める。
それ以外のプレースホルダー（{give} {keep} など、画面ごとに決まる値）はそのまま残し、
ページ側で fill(text, give=..., keep=...) を使って埋める。
テンプレートには文言を書かず、必ずここを経由する（設計書 §8）。
"""
from . import en, ja

_TEXTS = dict(en=en.TEXT, ja=ja.TEXT)


class _Keep(dict):
    """format_map 用: 未知のキーは {key} のまま残す。"""

    def __missing__(self, key):
        return '{' + key + '}'


def fill(value, **kwargs):
    """文字列（またはその入れ子）のプレースホルダーを kwargs で埋める。未知のキーは残す。"""
    if isinstance(value, str):
        return value.format_map(_Keep(kwargs))
    if isinstance(value, dict):
        return {k: fill(v, **kwargs) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, **kwargs) for v in value]
    return value


def texts(player):
    cfg = player.session.config
    lang = player.field_maybe_none('lang') or cfg.get('lang', 'ja')
    fmt = dict(
        endowment=f"{cfg['endowment']:,}",
        currency=cfg['currency_label'],
        fee=f"{cfg['participation_fee_yen']:,}",
        check_amount=f"{cfg.get('check_give', 300):,}",
        step=f"{cfg['dg_step']:,}",
    )
    return fill(_TEXTS[lang], **fmt)
