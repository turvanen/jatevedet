#!/usr/bin/env python3

"""
THL:n julkaiseman koronaviruksen jätevesiseurantatilaston käsittely ja visualisointi.

(c) turvanen 2022
https://github.com/turvanen/jatevedet
https://twitter.com/turvanen
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.dates import WeekdayLocator, MO
from matplotlib.ticker import AutoMinorLocator
from scipy import interpolate, signal


def valmistele_data(data, tasoita_kw=None):
    df = data.copy()

    # Lyhennetään eräiden puhdistamojen ja paikkakuntien nimet
    df.loc[df["Puhdistamon sijainti"] == "Maarianhamina - Mariehamn", "Puhdistamon sijainti"] = "Maarianhamina"
    df.loc[df["Puhdistamo"] == "Seinäjoenkeskuspuhdistamo", "Puhdistamo"] = "keskuspuhdistamo"
    df.loc[df["Puhdistamo"] == "Salonkeskuspuhdistamo", "Puhdistamo"] = "keskuspuhdistamo"

    # Yhdistetään puhdistamon paikkakunta ja nimi
    df["Puhdistamo"] = df["Puhdistamon sijainti"] + ", " + df["Puhdistamo"]

    # Muunnetaan negatiiviset ja määritysrajan alittavat havainnot numeerisiksi
    df.loc[df["Koronavirustulos näytteestä"] == 'ei havaittu', "Virtaamakorjattu RNA-lukumäärä"] = 1
    df.loc[df["Koronavirustulos näytteestä"] == 'tulos epävarma', "Virtaamakorjattu RNA-lukumäärä"] = 10
    df.loc[
        df["Koronavirustulos näytteestä"] == 'havaittu, alle määritysrajan', "Virtaamakorjattu RNA-lukumäärä"] = 100

    # Epävarmuustekijöitä sisältävät mittaukset per päivä (luetaan myös tiedon puuttuminen epävarmuustekijäksi)
    epvt_n = df.pivot(index="Näytteen päivämäärä",
                      columns="Puhdistamo",
                      values="Epävarmuustekijät"
                      ).count(axis=1)

    # Suoritetut mittaukset per päivä
    mittaukset_n = df.pivot(index="Näytteen päivämäärä",
                            columns="Puhdistamo",
                            values="Virtaamakorjattu RNA-lukumäärä"
                            ).count(axis=1)

    # Ryhmitellään sarakkeet puhdistamoittain
    df2 = df.pivot(index="Näytteen päivämäärä", columns="Puhdistamo")
    mittauspvt = np.array(df2.index)

    # Kaikki puhdistamot
    puhdistamot = df2.columns.levels[1]

    # Lasketaan trendit
    tasoita_kw_alkuarvot = {}
    if tasoita_kw is not None:
        tasoita_kw_alkuarvot.update(tasoita_kw)
    df2 = tasoita(df2, puhdistamot, **tasoita_kw_alkuarvot)

    # Lasketaan normalisoidut RNA-lukumäärät ja trendit
    scales = 1 / np.nanmax(df2["Trendi"], axis=0).reshape([1, -1])
    src_cols = ["Virtaamakorjattu RNA-lukumäärä",
                "Trendi",
                "Ekstrapoloitu trendi"]
    new_cols = ["Normalisoitu RNA-lkm",
                "Normalisoitu trendi",
                "Normalisoitu ekstrapoloitu trendi"]
    for A, B in zip(src_cols, new_cols):
        df2 = df2.join(pd.DataFrame(np.array(df2[A]) * scales,
                                    columns=pd.MultiIndex.from_product([[B], df2.columns.levels[1]]),
                                    index=df2.index))

    # Rajataan tarkastelu vain osaan puhdistamoista
    valitut_puhdistamot = valitse_puhdistamot(df2)

    return df2, mittauspvt, mittaukset_n, epvt_n, valitut_puhdistamot


def jakaumakaavio(df, dates, mittaukset_n, epvt_n, puhdistamot, keskiarvot=None, painotetut_ka=None, xlim_kw=None,
                  ylim_kw=None, logscale=False, figsize=(8, 5), dpi=None, subplots_adjust_kw=None, alatunniste_kw=None):
    fig, (ax_dist, ax_n) = plt.subplots(2, 1, figsize=figsize, dpi=dpi, sharex="all", gridspec_kw={'height_ratios': [9, 1]})

    # Mittaukset eivät osu aina samalle päivälle, joten täydennetään puuttuva data jakaumaa varten
    idata = df.loc[dates, "Normalisoitu RNA-lkm"][puhdistamot]
    idata = idata.interpolate(method="linear", limit_direction="forward", limit_area=None, limit=2, axis=0)

    # Jakauman värialueet
    cmap_dist = matplotlib.cm.get_cmap('plasma')
    label_postfix = " puhdistamoista"
    for p in [0, 10, 25, 50, 75, 90]:
        lower_interp = interpolate.PchipInterpolator(dates, np.log10(np.nanpercentile(idata, p / 2, axis=1)))
        upper_interp = interpolate.PchipInterpolator(dates, np.log10(np.nanpercentile(idata, 100 - p / 2, axis=1)))
        dates_interp = np.arange(dates[0], dates[-1] + 1, np.timedelta64(1, "h"), dtype=dates.dtype)
        ax_dist.fill_between(dates_interp,
                             10 ** lower_interp(dates_interp),
                             # 10**lower_interp(dates),
                             10 ** upper_interp(dates_interp),
                             # 10**upper_interp(dates),
                             # step="mid",
                             color=cmap_dist(1 - p / 120),
                             label=f"{100 - p}%{label_postfix}"
                             )
        label_postfix = ""

    # Mediaanipisteet
    ax_dist.plot(dates, np.nanmedian(idata, axis=1), ".", color=cmap_dist(0),
                 label="puhdistamojen mediaani\nmittauspäivänä")

    # Keskiarvokäyrät
    if keskiarvot:
        ax_dist.plot(df.index, keskiarvot[0], "-", color="k", label="trendien keskiarvo")
    if painotetut_ka:
        prefix = ""
        ennakko = None
        if not keskiarvot:
            prefix = "trendien keskiarvo,\n"
            ennakko = "ennakkoarvio"
        ax_dist.plot(df.index, painotetut_ka[0], "-", color="k", alpha=0.5, label=prefix + "asiakasmääräpainotettu")
        ax_dist.plot(df.index, painotetut_ka[1], "--", color="k", alpha=0.5, label=ennakko)
    if keskiarvot:
        ax_dist.plot(df.index, keskiarvot[1], "--", color="k", label="ennakkoarvio")

    # Kaavion asetuksia
    xlim_kw_defaults = {}
    if xlim_kw is not None:
        xlim_kw_defaults.update(xlim_kw)
    plt.xlim(**xlim_kw_defaults)

    if logscale:
        ylim_kw_defaults = {"bottom": 5e-5}
        if ylim_kw is not None:
            ylim_kw_defaults.update(ylim_kw)
        ax_dist.set_ylim(**ylim_kw_defaults)
        ax_dist.set_yscale("log")
    else:
        ylim_kw_defaults = {"bottom": 0, "top": 2}
        if ylim_kw is not None:
            ylim_kw_defaults.update(ylim_kw)
        ax_dist.set_ylim(**ylim_kw_defaults)

    ax_dist.legend(loc="upper left")
    ax_dist.set_ylabel("Normalisoitu virtaamakorjattu RNA-lkm")
    ax_dist.set_title(f"Virtaamakorjattu RNA-lukumäärä suhteessa puhdistamon trendin maksimiin")

    ax_dist.xaxis.set_minor_locator(WeekdayLocator(byweekday=MO))
    if not logscale:
        ax_dist.yaxis.set_minor_locator(AutoMinorLocator(n=2))
    ax_dist.grid(which="major", axis="both", c="k", alpha=0.1)
    ax_dist.grid(which="minor", axis="both", c="k", linestyle="-", alpha=0.05)

    # Epävarmuustekijöiden pylväskaavio
    cmap_n = matplotlib.cm.get_cmap('YlGnBu')
    barwidth = .9
    ax_n.bar(dates, mittaukset_n, width=barwidth, label="päivän mittausten lkm", color=cmap_n(0.5))
    ax_n.bar(dates, epvt_n, width=barwidth, label="joissa epävarmuustekijöitä tai tieto niistä puuttuu",
             color=cmap_n(1.0))
    ax_n.tick_params(which="both", left=False, labelleft=False, right=True, labelright=True)
    ax_n.legend(bbox_to_anchor=(0, -2, 1, 0), borderaxespad=0., loc="upper center", ncol=2)
    ax_n.grid(which="major", axis="both", c="k", alpha=0.1)
    ax_n.grid(which="minor", axis="x", c="k", linestyle="-", alpha=0.05)

    plt.xticks(rotation=30, ha="right")

    if alatunniste_kw is None: alatunniste_kw = {}
    alatunniste_kaavioon(**alatunniste_kw)

    subplots_adjust_kw_defaults = {"hspace": .050, "top": .929, "bottom": .245, "left": .094, "right": .947}
    if subplots_adjust_kw is not None:
        subplots_adjust_kw_defaults.update(subplots_adjust_kw)
    fig.subplots_adjust(**subplots_adjust_kw_defaults)

    return fig, (ax_dist, ax_n)


def trendipinokaavio(df, puhdistamot, xlim_kw=None, figsize=(8, 5), dpi=None, subplots_adjust_kw=None, alatunniste_kw=None):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ycoeff = -.20
    cmap = matplotlib.cm.get_cmap('Dark2')
    yticks = []
    yticklabels = []
    for i, p in enumerate(puhdistamot):
        trendi = df["Normalisoitu trendi", p]
        trendi_extrap = df["Normalisoitu ekstrapoloitu trendi", p]
        mittaukset = df["Normalisoitu RNA-lkm", p].dropna()
        y = ycoeff * i
        yticks.append(y)
        yticklabels.append(p)
        color = cmap((i % 8) / 8)
        if i == 0:
            trend_legend = "trendi"
            extrap_legend = "trendin ennakkoarvio"
            data_legend = "mittaustulos"
        else:
            trend_legend = None
            extrap_legend = None
            data_legend = None
        plt.plot(mittaukset.index, y + mittaukset, ".", c=color, alpha=.3, label=data_legend)
        plt.plot(df.index, y + trendi, "-", c=color, label=trend_legend)
        plt.plot(df.index, y + trendi_extrap, "-", c=color, alpha=.5, label=extrap_legend)
        plt.hlines(y, df.index[0], df.index[-1] + np.timedelta64(7, "D"),
                   linestyle="-", color=color, alpha=0.5, linewidth=.9)
    plt.yticks(yticks, yticklabels, fontsize=8)

    xlim_kw_defaults = {}
    if xlim_kw is not None:
        xlim_kw_defaults.update(xlim_kw)
    plt.xlim(**xlim_kw_defaults)

    plt.ylim(bottom=yticks[-1] + .25 * ycoeff, top=1.25)
    ax.xaxis.set_minor_locator(WeekdayLocator(byweekday=MO))
    plt.xticks(rotation=30, ha="right")
    plt.grid(which="major", axis="x", c="k", alpha=0.2)
    plt.grid(which="minor", axis="x", c="k", linestyle="-", alpha=0.1)
    plt.title(f"Virtaamakorjattu RNA-lkm suhteessa puhdistamon trendin maksimiin")
    plt.legend()

    if alatunniste_kw is None: alatunniste_kw = {}
    alatunniste_kaavioon(**alatunniste_kw)

    subplots_adjust_kw_defaults = {"top": .927, "bottom": .157, "left": .238, "right": .981}
    if subplots_adjust_kw is not None:
        subplots_adjust_kw_defaults.update(subplots_adjust_kw)
    fig.subplots_adjust(**subplots_adjust_kw_defaults)

    return fig, ax


def trendikaavio(df, puhdistamot, keskiarvot=None, painotetut_ka=None, xlim_kw=None, ylim_kw=None, logscale=False,
                 figsize=(8, 5), dpi=None, subplots_adjust_kw=None, alatunniste_kw=None):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    cmap = matplotlib.cm.get_cmap('Dark2')
    for i, p in enumerate(puhdistamot):
        trendi = df["Normalisoitu trendi", p]
        trendi_extrap = df["Normalisoitu ekstrapoloitu trendi", p]
        mittaukset = df["Normalisoitu RNA-lkm", p].dropna()
        color = cmap((i % 8) / 8)
        if i == 0:
            trend_legend = f"{p}, trendi"
            extrap_legend = "trendin ennakkoarvio"
            data_legend = "mittaustulos"
        else:
            trend_legend = p
            extrap_legend = None
            data_legend = None
        plt.plot(mittaukset.index, mittaukset, ".", c=color, alpha=.3, label=data_legend)
        plt.plot(df.index, trendi_extrap, "-", c=color, alpha=.5, label=extrap_legend)
        plt.plot(df.index, trendi, "-", c=color, label=trend_legend)

    if keskiarvot:
        plt.plot(df.index, keskiarvot[0], "-", color="k", label="maan trendien keskiarvo")
    if painotetut_ka:
        prefix = ""
        ennakko = None
        if not keskiarvot:
            prefix = "maan trendien keskiarvo,\n"
            ennakko = "ennakkoarvio"
        plt.plot(df.index, painotetut_ka[0], "-", color="k", alpha=0.5, label=prefix + "asiakasmääräpainotettu")
        plt.plot(df.index, painotetut_ka[1], "--", color="k", alpha=0.5, label=ennakko)
    if keskiarvot:
        plt.plot(df.index, keskiarvot[1], "--", color="k", label="ennakkoarvio")

    xlim_kw_defaults = {}
    if xlim_kw is not None:
        xlim_kw_defaults.update(xlim_kw)
    plt.xlim(**xlim_kw_defaults)

    if logscale:
        ylim_kw_defaults = {"bottom": 5e-5}
        if ylim_kw is not None:
            ylim_kw_defaults.update(ylim_kw)
        ax.set_ylim(**ylim_kw_defaults)
        ax.set_yscale("log")
    else:
        ylim_kw_defaults = {"bottom": 0}
        if ylim_kw is not None:
            ylim_kw_defaults.update(ylim_kw)
        ax.set_ylim(**ylim_kw_defaults)

    ax.xaxis.set_minor_locator(WeekdayLocator(byweekday=MO))
    if not logscale:
        ax.yaxis.set_minor_locator(AutoMinorLocator())
    plt.xticks(rotation=30, ha="right")
    plt.grid(which="major", axis="both", c="k", alpha=0.2)
    plt.grid(which="minor", axis="both", c="k", linestyle="-", alpha=0.1)
    ax.set_ylabel("Normalisoitu virtaamakorjattu RNA-lkm")
    plt.title(f"Virtaamakorjattu RNA-lukumäärä suhteessa puhdistamon trendin maksimiin")
    plt.legend()

    if alatunniste_kw is None: alatunniste_kw = {}
    alatunniste_kaavioon(**alatunniste_kw)

    subplots_adjust_kw_defaults = {"top": .927, "bottom": .157, "left": .090, "right": .981}
    if subplots_adjust_kw is not None:
        subplots_adjust_kw_defaults.update(subplots_adjust_kw)
    fig.subplots_adjust(**subplots_adjust_kw_defaults)

    return fig, ax


def alatunniste_kaavioon(left_txt="Jätevesitilasto ©THL (lisenssillä CC BY 4.0)",
                         center_txt="",
                         right_txt="Luotu ohjelmalla https://github.com/turvanen/jatevedet"):
    txt_color = (.5, .5, .5)
    if left_txt is not None:
        plt.figtext(0.01, 0.01, left_txt, wrap=True, ha="left", va="bottom", color=txt_color, fontsize=8)
    if center_txt is not None:
        plt.figtext(0.5, 0.01, center_txt, wrap=True, ha="center", va="bottom", color=txt_color, fontsize=8)
    if right_txt is not None:
        plt.figtext(0.99, 0.01, right_txt, wrap=True, ha="right", va="bottom", color=txt_color, fontsize=8)


def tasoita(df, puhdistamot, M_days=9*7, reindex_freq_hours=12):
    assert 24 % reindex_freq_hours == 0
    df2 = df.reindex(pd.date_range(start=df.index.min(), end=df.index.max(), freq=f"{reindex_freq_hours}H"))
    M = M_days * (24 // reindex_freq_hours)
    M += 1 - (M % 2)
    win = signal.windows.blackman(M)
    win = win / np.sum(win)

    print("Ikkunan leveys")
    print(f"  Ikkunan painosta 100%: {(M - 1) * reindex_freq_hours / 24} päivää (kertoimia {M} kpl)")
    win_int = np.cumsum(win)
    for interval in [50, 80, 90, 95, 99]:
        margin = (1 - interval / 100) / 2
        first = np.argwhere(win_int <= margin)[-1, 0]
        last = np.argwhere(win_int > 1 - margin)[0, 0]
        L = (last - first - 1) * reindex_freq_hours / 24
        print(f"  Ikkunan painosta {np.sum(win[first:last]) * 100:.2f}% >= {interval}%: {L} päivää")

    for i, p in enumerate(puhdistamot):
        # print(f"{i + 1}/{len(puhdistamot)}: {p}")
        sig = np.array(np.log10(df2["Virtaamakorjattu RNA-lukumäärä", p]))
        filt, filt_extrap = nanconv(sig, win)
        df2["Trendi", p] = 10 ** filt
        df2["Ekstrapoloitu trendi", p] = 10 ** filt_extrap
    return df2


def trendien_keskiarvot(df, puhdistamot):
    trendit = df["Normalisoitu trendi"][puhdistamot]
    trendit_extrap = df["Normalisoitu ekstrapoloitu trendi"][puhdistamot]

    trendit_ka = trendit.mean(axis=1)
    trendit_ka_extrap = trendit_extrap.mean(axis=1)

    asiakaslkm = df["Puhdistamon asiakasmäärä"][puhdistamot].interpolate(method="pad").mask(
        np.logical_and(df["Normalisoitu trendi"][puhdistamot].isna(),
                       df["Normalisoitu ekstrapoloitu trendi"][puhdistamot].isna())
    )
    painot = np.array(asiakaslkm.div(asiakaslkm.sum(axis=1, min_count=1), axis=0))
    painotettu_ka = np.nansum(np.array(trendit) * painot, axis=1)
    painotettu_ka_extrap = np.nansum(np.array(trendit_extrap) * painot, axis=1)
    painotettu_ka = np.where(painotettu_ka == 0.0, np.NaN, painotettu_ka)
    painotettu_ka_extrap = np.where(painotettu_ka_extrap == 0.0, np.NaN, painotettu_ka_extrap)

    return (trendit_ka, trendit_ka_extrap), (painotettu_ka, painotettu_ka_extrap)


def valitse_puhdistamot(df):
    prioriteetti = []
    puhdistamot = []
    for p in df.columns.levels[1]:
        vals = len(df.query("index > '2021-07'")["Virtaamakorjattu RNA-lukumäärä", p].dropna())
        if vals <= 0:
            continue
        puhdistamot.append(p)
        prioriteetti.append(np.nansum(df.loc["2022-04-01":, ("Normalisoitu trendi", p)]) +
                            0 * np.nansum(df.loc["2022-04-01":, ("Normalisoitu ekstrapoloitu trendi", p)]))
    puhdistamot = np.array(puhdistamot)
    ind = np.argsort(prioriteetti)
    puhdistamot = list(puhdistamot[ind])
    return puhdistamot[::-1]


def nanconv(X: np.ndarray, w: np.ndarray) -> (np.ndarray, np.ndarray):
    M = len(w)
    M_half = (M - 1) // 2
    Y = np.full(X.size, np.NaN)
    Yextra = np.full(X.size, np.NaN)
    for i in range(M_half, len(X) - M_half):
        Y[i] = nanwmean(X[i - M_half:i + M_half + 1], w)
    Yextra[-M_half - 1] = Y[-M_half - 1]
    for i in range(len(X) - M_half, len(X)):
        Yextra[i] = nanwmean(X[i - M_half:], w[:len(X) - M_half - i - 1])
    return Y, Yextra


def nanwmean(x: np.ndarray, w: np.ndarray):
    prod = x * w
    vals = np.logical_not(np.isnan(prod))
    s = np.nansum(prod)
    ws = np.sum(w[vals])
    if ws > 0:
        return s / ws
    return np.NaN
