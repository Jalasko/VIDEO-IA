# VIDEO-IA — « Bath Time Song »

Comptine animée de 68 secondes : **Lilo** (petite fille de 3 ans) et **Bobo** (bébé éléphant bleu) prennent leur bain, en 6 plans.

Résultats :
- [`output/bath_time_song.mp4`](output/bath_time_song.mp4) : 1920×1080 (YouTube), 30 i/s, H.264 + AAC
- [`output/bath_time_song_tiktok.mp4`](output/bath_time_song_tiktok.mp4) : 1080×1920 vertical (TikTok, Reels, Shorts), avec une caméra qui suit les personnages et le texte placé hors des zones de l'interface TikTok

## Comment c'est fabriqué

Tout est généré par du code dans cet environnement, sans service de génération vidéo :

| Élément | Technique |
|---|---|
| Images | Rendu « 3D doux » maison en Python/numpy (`bath_time/gfx.py`) : formes arrondies ombrées comme du plastique, reflets spéculaires, lumière de contour, flou d'arrière-plan, bloom et vignettage |
| Personnages | Une fonction par personnage (`bath_time/characters.py`), donc le même design dans tous les plans |
| Mise en scène | 6 plans avec caméra animée (zooms et travellings doux) dans `bath_time/scenes.py` |
| Musique | Synthétisée en numpy à 100 BPM : xylophone, ukulélé (Karplus-Strong), basse, claps, shaker (`bath_time/music.py`) |
| Voix chantée | Synthèse vocale neuronale Kokoro (voix féminine `af_heart`), puis le vocodeur WORLD recale chaque syllabe sur la note et le rythme de la mélodie (`bath_time/vocals.py`) |
| Bruitages | Éclaboussures, bulles qui éclatent, canard qui couine, eau qui coule, douche de la trompe, « boing » de la grenouille, carillons d'étoiles |
| Synchro | `bath_time/song.py` contient la mélodie, les paroles et la ligne de temps commune. La bouche de Lilo, les paroles karaoké, les actions et les bruitages suivent les mêmes instants |

## Reconstruire la vidéo

```bash
pip install numpy pillow soundfile pyworld kokoro-onnx
# modèles Kokoro : kokoro-v1.0.onnx + voices-v1.0.bin
# https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
python3 build.py --voice-dir /chemin/vers/kokoro
python3 build.py --voice-dir ... --vertical            # version TikTok 9:16
python3 build.py --voice-dir ... --start 14 --end 20   # un extrait
python3 build.py --voice-dir ... --mux-only            # refaire seulement l'audio
```

Il faut aussi `ffmpeg`. Le rendu complet prend environ 20 minutes sur 4 cœurs.

## Limites par rapport au prompt d'origine

- **Pas un vrai rendu Pixar ni de la 4K** : c'est une imitation 2,5D. Pour un rendu 3D cinématographique, il faut un modèle de génération vidéo (Veo, Runway, Kling, Sora…). Les prompts plan par plan sont prêts dans [`prompts/shots.md`](prompts/shots.md).
- **La voix chantée est synthétique** : elle suit bien les notes et le rythme, mais on entend que c'est une voix d'ordinateur, pas une chanteuse.
