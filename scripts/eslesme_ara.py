import json

cats = json.load(open('/mnt/c/Kuroshin/kurowatch/scripts/site_catalogs.json'))
rg = cats.get('ragnarscans', {})
hy = cats.get('hayalistic', {})
rg_slugs = list(rg.keys())
hy_slugs = list(hy.keys())

def in_rg(slug): return slug in rg_slugs
def in_hy(slug): return slug in hy_slugs

def findany_rg(kws):
    return [s for s in rg_slugs if any(k in s for k in kws)]
def findany_hy(kws):
    return [s for s in hy_slugs if any(k in s for k in kws)]

print('=== MANGA/MANHWA RG/HY ONERI DOGRULAMA ===')
suggestions = [
    ('4',  'Buyu Imparatoru',  'rg', 'buyu-imparatoru'),
    ('4',  'Buyu Imparatoru',  'hy', 'buyu-imparatoru'),
    ('8',  'Geri Donen Buyucu', 'hy', 'seni-geri-dondurmek'),
    ('92', 'Kahramanin Donusu', 'hy', 'kahraman-katili'),
    ('45', 'Kilic Hanesi', 'hy', 'kilic-kralinin-fantezi-dunyasinda-hayatta-kalma-hikayesi'),
    ('153','Martial Divine Demon','rg','the-martial-genius-who-remembers-everything'),
    ('1',  'Martial Peak','rg','the-martial-genius-who-remembers-everything'),
    ('19', 'Murim Login','rg','murim-psychopath'),
    ('64', 'Regresor Kilavuzu','rg','regressor-instruction-manual'),
    ('64', 'Regresor Kilavuzu','hy','ben-regresor-degilim'),
    ('41', 'Strongest Fighter','rg','the-strongest-god-king'),
    ('23', 'Seckinin Ikinci Yasami','rg','seckinin-ikinci-yasami'),
    ('23', 'Seckinin Ikinci Yasami','hy','seckinin-ikinci-yasami'),
    ('70', 'Oyuncunun Son Sansi','hy','oyunculari-fethet'),
    ('56', 'Yildiz Hocasi Baek','hy','yildiz-tozundan'),
    ('32', 'The Max Level Hero','rg','the-strongest-god-king'),
    ('83', 'Regressing King Power','rg','a-dragonslayers-peerless-regression'),
]
for id_, name, site, slug in suggestions:
    if site == 'rg':
        found = in_rg(slug)
        url = rg.get(slug, 'YOK')
    else:
        found = in_hy(slug)
        url = hy.get(slug, 'YOK')
    marker = 'OK' if found else 'XX'
    print(f'{marker} [{id_}] {name} ({site}): {slug} -> {url}')

print()
print('=== MANGA ARAMA (oneri olmayanlar) ===')
checks = [
    ('134','A Regressor Cultivation', ['regressor', 'cultivation']),
    ('3',  'Above All Gods', ['all-gods', 'tum-tanri']),
    ('12', 'Above Ten Thousand People', ['ten-thousand', 'on-bin']),
    ('136','Absolute Reign', ['absolute-reign', 'mutlak-hakimiyet']),
    ('137','After Ten Millennia in Hell', ['millennia', 'cehennem', 'on-bin-yil']),
    ('94', 'Cultivator Against Hero', ['cultivator', 'korsanlar']),
    ('71', 'Damn Reincarnation', ['damn', 'lanet-reenkarn', 'lanetli-yeniden']),
    ('26', 'Deli Muhendis', ['deli-muhendis']),
    ('145','Doom Breaker', ['doom-breaker']),
    ('146','Dungeon Odyssey', ['dungeon-odyssey']),
    ('77', 'Dovus Tanrisinin Donusu', ['dovus-tanri', 'savasan-tanri']),
    ('13', 'Dunyanin En Iyi Muhendisi', ['muhendis', 'dunyanin']),
    ('20', 'FFF-Class Trashero', ['fff-class', 'trashero', 'cezali-kahraman']),
    ('93', 'Forced Villain Son-in-Law', ['villain', 'kotuler']),
    ('24', 'Hardcore Leveling Warrior', ['hardcore', 'leveling']),
    ('5',  'I Am Cultivation Bigshot', ['cultivation-bigshot', 'buyuk-usta']),
    ('54', 'I Just Want To Be Killed', ['oldurulmek', 'killed']),
    ('149','I Killed Main Player', ['oyuncuyu-oldur']),
    ('51', 'I Reincarnated Crazed Heir', ['crazed', 'deli-varis']),
    ('78', 'Im Not That Kind of Talent', ['yetenek-degil', 'o-tur-yetenek']),
    ('22', 'Juujika no Rokunin', ['juujika']),
    ('76', 'Kage no Jitsuryokusha', ['kage-no-jitsury']),
    ('150','Latna Saga', ['latna']),
    ('151','Level Up with the Gods', ['tanrilarla', 'level-up-gods']),
    ('84', 'Library of Heaven Path', ['cennet-kitapligi', 'library']),
    ('152','Lout of Count Family', ['kontes-ailesi', 'copluk']),
    ('155','Mercenary Enrollment', ['paralı-asker', 'mercenary']),
    ('156','My Avatars Path', ['avatar', 'temsilcim']),
    ('157','My Blasted Reincarnated', ['lanetli-yeniden', 'blasted']),
    ('158','My S-Class Hunters', ['s-sinif', 's-class-hunters']),
    ('18', 'Nano Machine', ['nano-machine', 'nano']),
    ('160','Nebula Civilization', ['bulutsusu', 'nebula']),
    ('161','Omniscient Readers', ['omniscient', 'her-seyi-bilen']),
    ('69', 'Overpowered Sword', ['guclu-kilic', 'overpowered-sword']),
    ('36', 'Player Who Returned 10000', ['geri-donen', 'on-bin-yil-sonra']),
    ('61', 'Return of Shattered Constellation', ['yildiz', 'ufalanmis']),
    ('171','Returning With Nothing', ['hicbir-seysiz', 'nothing']),
    ('172','Revenge Baskerville', ['baskerville']),
    ('176','SSS-Class Suicide Hunter', ['intihar-avcisi', 'sss-class-hunter']),
    ('173','Second Life Ranker', ['ikinci-hayat', 'second-life']),
    ('174','Shadow of Supreme', ['golge-hakim', 'shadow-supreme']),
    ('68', 'Sokakta Hayatta Kalma', ['sokak']),
    ('177','Standard of Reincarnation', ['yeniden-dogus-standar', 'standard-reinkarnasyon']),
    ('15', 'Scholars Reincarnation', ['alimlerin', 'scholar']),
    ('16', 'The Beginning After the End', ['beginning-after-end', 'sonun-baslangici']),
    ('17', 'The Tutorial Tower', ['tutorial-tower', 'ogretici-kule']),
    ('58', 'The World After the End', ['dunyanin-sonu', 'world-after-end']),
    ('34', 'Top Tier Providence', ['top-tier', 'uzerine-kader']),
    ('29', 'Tower Into Clouds', ['bulut-kulesi', 'tower-clouds']),
    ('74', 'Yetenek Yutan Sihirbaz', ['yetenek-yutan']),
    ('88', 'Yildirim Bicagi Ustasi', ['yildirim-bicagi']),
    ('59', 'Magdur Siralamacinin Donusu', ['magdur-siralama', 'magdur']),
    ('91', 'Oyun Obu Familia', ['familia']),
    ('90', 'Semalarin Kilici', ['semalarin-kilici']),
    # Manhwa
    ('10', 'A Returners Magic', ['returners-magic', 'donus-sihirbazi']),
    ('138','Bad Born Blood', ['bad-born', 'kotu-kan']),
    ('40', 'Bug Player', ['bug-player', 'hata-oyuncusu']),
    ('139','Cassmire', ['cassmire']),
    ('140','Cassmire Loyal Sword', ['cassmire-loyal']),
    ('141','Cheonhwa Archive', ['cheonhwa']),
    ('142','Chronicles Doomed Prodigy', ['chronicles-doom', 'lanetli-dahi']),
    ('143','Chronicles Demon Faction', ['demon-faction', 'seytan-hizip']),
    ('144','Demon King Royal Class', ['demon-king-royal']),
    ('75', 'I Became Tyrant Defense', ['tyrant', 'savunma-oyunu', 'bek-etme']),
    ('53', 'Memorize', ['memorize']),
    ('86', 'My Insanely Competent Underlings', ['yetenekli-astlar', 'underlings']),
    ('80', 'Never Die Extra', ['never-die', 'olmez-figüran']),
    ('87', 'Raising Newbie Heroes', ['newbie-heroes', 'yeni-kahraman']),
    ('46', 'Rankers Return Remake', ['rankers-return', 'ranker-donusu']),
    ('165','Reborn as Scholar', ['scholar', 'alim']),
    ('166','Reincarnated Murim Lord', ['murim-lord', 'murim-efendisi']),
    ('52', 'Reincarnation Murim Ranker', ['murim-ranker', 'murim-klan']),
    ('169','Return Disaster Class Hero', ['disaster', 'felaket-kahraman']),
    ('47', 'Return Mount Hua Sect', ['mount-hua', 'hua-sekt']),
    ('170','Return of War God', ['savaş-tanrisi-donusu', 'war-god']),
    ('30', 'Return to Player', ['return-to-player', 'oyuncuya-don']),
    ('73', 'Revenge Iron-Blooded Sword', ['iron-blooded', 'demir-kanli']),
    ('57', 'SSS-Class Suicide Hunter', ['intihar-avcisi', 'sss-class']),
    ('63', 'Seoul Station Necromancer', ['seoul', 'buyucu']),
    ('48', 'Heavenly Demon Cant Normal Life', ['cennet-seytan', 'normal-yasam']),
    ('89', 'Unbeatable Dungeon Lazy Boss', ['tembel-patron', 'lazy-boss']),
    ('195','The World After Fall', ['world-after-fall', 'catismanin-sonrasi']),
    ('197','Too Many Heroes', ['cok-fazla-kahraman', 'too-many-heroes']),
    ('79', 'Villain Unrivaled', ['villain-unrivaled', 'kotunun-ustunde']),
    ('200','Yongsa High Dungeon Raiders', ['yongsa', 'dungeon-raiders']),
]

for id_, name, kws in checks:
    rg_res = findany_rg(kws)
    hy_res = findany_hy(kws)
    if rg_res or hy_res:
        print(f'OK [{id_}] {name}:')
        for r in rg_res[:2]:
            print(f'   RG -> {r} = {rg[r]}')
        for h in hy_res[:2]:
            print(f'   HY -> {h} = {hy[h]}')
