"""
Grafikkinnstillinger for 3D-viewer.

Juster verdiene her for å endre kvalitet og ytelse.
Høyere verdier = bedre grafikk, men tyngre for systemet.
"""

# =====================================================================
# ANTI-ALIASING (MSAA)
# Antall samples per piksel. Fjerner taggete kanter.
# Verdier: 0 (av), 2, 4, 8, 16
# Ytelse: HØY — dette er den tyngste innstillingen for GPU-en
# =====================================================================
MSAA_SAMPLES = 8

# =====================================================================
# DEPTH BUFFER
# Presisjon for dybdetest (unngår z-fighting/flimring).
# Verdier: 16, 24, 32
# Ytelse: LITEN
# =====================================================================
DEPTH_BUFFER_SIZE = 24

# =====================================================================
# MESH-OPPLØSNING
# Antall segment på kurvede deler. Flere = glattere, men flere polygoner.
# Ytelse: MIDDELS
# =====================================================================

# Håndtak-grep (sylindrisk rør) — segment rundt sirkelen
# Anbefalt: 24 (lav), 48 (middels), 64 (høy)
LEVER_TUBE_SEGMENTS = 64

# Håndtak-grep — bue-segment (kvartssirkel fra skilt til rett del)
# Anbefalt: 10 (lav), 20 (middels), 30 (høy)
LEVER_BEND_SEGMENTS = 30

# Håndtak-skilt — hjørne-segment (avrunding per hjørne)
# Anbefalt: 8 (lav), 16 (middels), 24 (høy)
PLATE_CORNER_SEGMENTS = 24

# =====================================================================
# SMOOTH SHADING
# Interpolerer farger mellom flater for mjukere overgang.
# True = glatt (bra for kurver), False = flat (bra for skarpe kanter)
# Ytelse: LITEN
# =====================================================================
SMOOTH_CURVED_PARTS = True    # Håndtak-skilt og grep

# =====================================================================
# BELYSNING
# Styrer lys og materialfølelse.
# Ytelse: INGEN — bare matematiske verdier
# =====================================================================

# Ambient (grunnlys, alltid synlig) — 0.0 til 1.0
LIGHT_AMBIENT = 0.65

# Diffuse (retningsavhengig lys) — 0.0 til 1.0
LIGHT_DIFFUSE = 0.40

# Specular (glanspunkt/refleksjon) — 0.0 til 1.0
# 0 = matt, 0.25 = litt glans, 0.5 = blank
LIGHT_SPECULAR = 0.25

# Shininess (skarphet på glanspunkt) — 1 til 128
# Lavt = bred, diffus glans. Høyt = skarp, konsentrert glans.
LIGHT_SHININESS = 64.0

# Lysretning (normaliseres automatisk)
LIGHT_DIRECTION = (0.3, 0.6, 0.5)

# Kameraretning for spekulær beregning (normaliseres automatisk)
VIEW_DIRECTION = (0.0, 1.0, 0.3)

# Lysfaktorer per flateretning for bokser (karm, dørblad, vegg)
# Rekkefølge: bunn, topp, front(Y+), bak(Y-), venstre(X-), høyre(X+)
BOX_FACE_LIGHT = (0.52, 1.12, 0.98, 0.58, 0.68, 0.85)

# =====================================================================
# BAKGRUNN
# RGB-farge for 3D-vinduet (0-255)
# =====================================================================
BACKGROUND_COLOR = (50, 50, 55, 255)
