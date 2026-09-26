import socket, threading, json, time
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageOps

PRINTER_IP   = '192.168.100.101'
PRINTER_PORT = 9100
PORT         = 9000
FONT_PATH    = '/etc/gafflabel/font.ttc'
HTML_PATH    = '/root/flaggit.html'
W            = 320
SAFE_W       = 270
OFFSET_N     = -25
OFFSET_F     = 25
MAX_FONT     = 54
LINE2_RATIO  = 0.80
PERP_W       = 48

HTML = open(HTML_PATH, 'rb').read()

def fit_font(text, max_w, start, font_index=0):
    size = int(start)
    while size > 10:
        f = ImageFont.truetype(FONT_PATH, size, index=font_index)
        b = f.getbbox(text)
        if (b[2]-b[0]) <= max_w:
            return f, size
        size -= 1
    return ImageFont.truetype(FONT_PATH, 10, index=font_index), 10

def cx(text, font, offset):
    b = font.getbbox(text)
    return (W - (b[2]-b[0])) // 2 - b[0] + offset

def make_label(line1, line2, sep, font_size=MAX_FONT, pad=10, perp_text=None, bold=False):
    safe_w = SAFE_W - (PERP_W + 4 if perp_text else 0)
    fi = 1 if bold else 0
    font_l, sl = fit_font(line1, safe_w, font_size, fi)
    font_s, ss = fit_font(line2, safe_w, sl * LINE2_RATIO, fi) if line2 else (None, 0)
    b1  = font_l.getbbox(line1)
    th1 = b1[3] - b1[1]
    th2 = (font_s.getbbox(line2)[3] - font_s.getbbox(line2)[1]) if font_s else 0
    PAD    = pad
    GAP    = 8 if line2 else 0
    HALF_H = PAD + th1 + (GAP + th2 if line2 else 0) + PAD
    H      = HALF_H * 2 + sep

    def draw_perp(target, y_top):
        strip_w = PERP_W - 4
        avail   = HALF_H - 8
        pf, _ = fit_font(perp_text, avail, strip_w, 0)
        pb = pf.getbbox(perp_text)
        tw, th = pb[2]-pb[0], pb[3]-pb[1]
        h_img = Image.new('RGB', (avail, strip_w), 'white')
        tx = (avail - tw) // 2 - pb[0]
        ty = (strip_w - th) // 2 - pb[1]
        ImageDraw.Draw(h_img).text((tx, ty), perp_text, fill='black', font=pf)
        v_img = h_img.rotate(90, expand=True)
        x_sep = W - PERP_W - 1
        ImageDraw.Draw(target).line([(x_sep, y_top+4), (x_sep, y_top+HALF_H-4)], fill='#aaaaaa', width=1)
        px = x_sep + 2 + (PERP_W - 2 - v_img.width) // 2
        py = y_top + (HALF_H - v_img.height) // 2
        target.paste(v_img, (px, max(y_top, py)))

    img  = Image.new('RGB', (W, H), 'white')
    draw = ImageDraw.Draw(img)
    img1  = Image.new('RGB', (W, HALF_H), 'white')
    draw1 = ImageDraw.Draw(img1)
    draw1.text((cx(line1, font_l, OFFSET_F), PAD), line1, fill='black', font=font_l)
    if line2 and font_s:
        draw1.text((cx(line2, font_s, OFFSET_F), PAD+th1+GAP), line2, fill='black', font=font_s)
    if perp_text:
        draw_perp(img1, 0)
    img1 = img1.rotate(180)
    img.paste(img1, (0, 0))
    draw.line([(0, HALF_H + sep//2), (W, HALF_H + sep//2)], fill='black', width=1)
    draw.text((cx(line1, font_l, OFFSET_N), HALF_H + sep + PAD), line1, fill='black', font=font_l)
    if line2 and font_s:
        draw.text((cx(line2, font_s, OFFSET_N), HALF_H + sep + PAD+th1+GAP), line2, fill='black', font=font_s)
    if perp_text:
        draw_perp(img, HALF_H + sep)
    return img

def make_label_perp(line1, perp_text, sep, line2=None, label_padding=0, bold=False, max_half_px=430, cable_pad=100, show_name=None, show_name_invert=False, dominance='l1'):
    """All text rotated 90°. Padding goes between text and tag. Tag fixed distance from end."""
    fi = 1 if bold else 0
    BASE_PAD = 10 + cable_pad  # fold-side offset: base + cable diameter clearance
    END_PAD  = 10     # fixed free-end padding (tag always this far from paper end)
    TEXT_MARGIN = 10  # margin used for text height constraint (independent of cable_pad)
    BASE_GAP = 8      # fixed gap between text and tag before label_padding
    LINE_GAP = 8
    TARGET_HALF_PX = max_half_px
    max_text_w  = TARGET_HALF_PX - 10 - BASE_GAP - END_PAD  # use fixed base, cable_pad adds length not shrinks text
    max_total_h = W - 2 * TEXT_MARGIN

    # Map slider directly to font height — matches preview scaling (10%→100% of tape width)
    slider_frac = max(0.0, min(1.0, (max_half_px - 200) / 300))
    max_h_by_slider = max(10, int(max_total_h * (0.10 + 0.90 * slider_frac)))

    # Split tape width between line1 and line2 based on dominance
    if line2:
        r1 = 0.30 if dominance == 'l2' else (0.46 if dominance == 'equal' else 0.62)
        r2 = 0.62 if dominance == 'l2' else (0.46 if dominance == 'equal' else 0.30)
        max_h1 = min(int(max_total_h * r1), max_h_by_slider)
    else:
        r2 = 0.30
        max_h1 = min(max_total_h, max_h_by_slider)

    # Fit line1: largest font where height<=max_h1 and width<=max_text_w
    font_l = ImageFont.truetype(FONT_PATH, 10, index=fi)
    b1 = font_l.getbbox(line1)
    size = 10
    for size in range(max_h1, 10, -1):
        f = ImageFont.truetype(FONT_PATH, size, index=fi)
        b = f.getbbox(line1)
        if (b[3]-b[1]) <= max_h1 and (b[2]-b[0]) <= max_text_w:
            font_l = f; b1 = b; break

    line1_tape_len = b1[2] - b1[0]

    # Fit line2: sized by dominance ratio; width constrained to max_text_w
    font_s = None
    b2 = None
    if line2:
        max_h2 = int(max_total_h * r2)
        for size2 in range(max_h2, 10, -1):
            f = ImageFont.truetype(FONT_PATH, size2, index=fi)
            b = f.getbbox(line2)
            if (b[3]-b[1]) <= max_h2 and (b[2]-b[0]) <= max_text_w:
                font_s = f; b2 = b; break

    h1 = b1[3] - b1[1]
    h2 = (b2[3] - b2[1]) if b2 else 0
    total_text_h = h1 + (LINE_GAP + h2 if line2 and b2 else 0)
    text_tape_len = line1_tape_len

    # Tag: fixed size reference so MAIN and BACKUP always print same scale
    font_tag = None
    bt = None
    tag_tape_len = 0
    if perp_text:
        font_tag, _ = fit_font('BACKUP', SAFE_W, SAFE_W, 0)
        bt = font_tag.getbbox(perp_text)
        tag_tape_len = bt[3] - bt[1] + 8

    # Show name: slightly smaller than MB tag, outermost position
    font_sn = None
    bsn = None
    sn_tape_len = 0
    SN_GAP = 6
    if show_name:
        sn_h = int(SAFE_W * 0.55)
        font_sn, _ = fit_font(show_name, SAFE_W, sn_h, 0)
        bsn = font_sn.getbbox(show_name)
        sn_tape_len = bsn[3] - bsn[1] + 6

    # Layout: fold → BASE_PAD → label_padding → text → BASE_GAP+label_padding → [tag →] [SN_GAP + show_name →] END_PAD
    gap_to_tag = BASE_GAP + label_padding
    HALF_H = BASE_PAD + label_padding + text_tape_len + (gap_to_tag + tag_tape_len if perp_text else 0) + (SN_GAP + sn_tape_len if show_name else 0) + END_PAD
    H      = HALF_H * 2 + sep

    def draw_half(canvas, y_top, offset=0):
        h_main = Image.new('RGB', (text_tape_len, total_text_h), 'white')
        dh = ImageDraw.Draw(h_main)
        x1 = (text_tape_len - (b1[2]-b1[0])) // 2 - b1[0]
        dh.text((x1, -b1[1]), line1, fill='black', font=font_l)
        if line2 and font_s and b2:
            x2 = (text_tape_len - (b2[2]-b2[0])) // 2 - b2[0]
            dh.text((x2, h1 + LINE_GAP - b2[1]), line2, fill='black', font=font_s)
        v_main = h_main.rotate(-90, expand=True)
        mx = (W - v_main.width) // 2 + offset
        canvas.paste(v_main, (mx, y_top + BASE_PAD + label_padding))

        if perp_text and font_tag and bt:
            ty = y_top + BASE_PAD + label_padding + text_tape_len + gap_to_tag
            tw = bt[2] - bt[0]
            tx = (W - tw) // 2 - bt[0] + offset
            ImageDraw.Draw(canvas).text((tx, ty - bt[1]), perp_text, fill='black', font=font_tag)
        if show_name and font_sn and bsn:
            sn_y = y_top + BASE_PAD + label_padding + text_tape_len + gap_to_tag + (tag_tape_len if perp_text else 0) + SN_GAP
            snw = bsn[2] - bsn[0]
            snx = (W - snw) // 2 - bsn[0] + offset
            d = ImageDraw.Draw(canvas)
            if show_name_invert:
                d.rectangle([0, sn_y - 2, W, sn_y + sn_tape_len + 2], fill='black')
                d.text((snx, sn_y - bsn[1]), show_name, fill='white', font=font_sn)
            else:
                d.text((snx, sn_y - bsn[1]), show_name, fill='#555555', font=font_sn)

    img  = Image.new('RGB', (W, H), 'white')
    draw = ImageDraw.Draw(img)

    # Top half (mirrored — back of flag)
    img1 = Image.new('RGB', (W, HALF_H), 'white')
    draw_half(img1, 0, offset=OFFSET_F)
    img1 = img1.rotate(180)
    img.paste(img1, (0, 0))

    # Separator
    draw.line([(0, HALF_H + sep//2), (W, HALF_H + sep//2)], fill='black', width=1)

    # Bottom half (front of flag)
    draw_half(img, HALF_H + sep, offset=OFFSET_N)

    return img

def build_raster(img):
    bpl = 40
    basewidth = bpl * 8
    wpercent = basewidth / float(img.width)
    hsize = int(float(img.height) * float(wpercent))
    img = PIL.ImageOps.invert(img.convert('RGB'))
    img = img.convert(mode='1', dither=Image.FLOYDSTEINBERG).resize((basewidth, hsize))
    bytesarray = bytes(img.tobytes())
    buf = [0x1b, 0x40,
           0x1b, ord('*'), ord('r'), ord('A'),
           0x1b, ord('*'), ord('r'), ord('P'), ord('0'), 0x00,
           0x1b, ord('*'), ord('r'), ord('m'), ord('0'), 0x00]
    byte = 0
    for line in range(img.height):
        row = [ord('b'), bpl, 0]
        for b in range(bpl):
            row.append(bytesarray[byte])
            byte += 1
        buf.extend(row)
    buf.extend([0x1b, ord('*'), ord('r'), ord('B')])
    return bytearray(buf)

def print_labels(labels, sep, font_size=MAX_FONT):
    imgs = []
    for l in labels:
        if l.get('perp_mode'):
            imgs.append(make_label_perp(
                l['line1'],
                l.get('perp_text') or None,
                sep,
                line2=l.get('line2') or None,
                label_padding=int(l.get('label_padding', 0)),
                bold=bool(l.get('bold', False)),
                max_half_px=int(l.get('font_size', 430)),
                cable_pad=int(l.get('cable_pad', 100)),
                show_name=l.get('show_name') or None,
                show_name_invert=bool(l.get('show_name_invert', False)),
                dominance=l.get('dominance', 'l1')
            ))
        else:
            imgs.append(make_label(
                l['line1'], l.get('line2'), sep,
                int(l.get('font_size', font_size)),
                int(l.get('label_padding', 0)) + 10,
                l.get('perp_text') or None,
                bool(l.get('bold', False))
            ))
    buf = bytearray()
    for img in imgs:
        buf += build_raster(img)
        buf += bytes([0x1b, ord('*'), ord('r'), ord('E'), 1, 0x00])
    s = socket.socket()
    s.settimeout(10)
    s.connect((PRINTER_IP, PRINTER_PORT))
    time.sleep(0.5)
    s.sendall(bytes(buf))
    time.sleep(2)
    s.close()

def recv_full(conn):
    data = b''
    conn.settimeout(5)
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b'\r\n\r\n' in data:
                header_part = data.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
                cl = 0
                for line in header_part.split('\r\n'):
                    if line.lower().startswith('content-length:'):
                        cl = int(line.split(':',1)[1].strip())
                body = data.split(b'\r\n\r\n', 1)[1]
                while len(body) < cl:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    body += chunk
                return header_part, body
    except:
        pass
    return None, b''

def handle(conn):
    try:
        header_str, body = recv_full(conn)
        if not header_str:
            conn.close()
            return

        first_line = header_str.split('\r\n')[0]
        method = first_line.split()[0]
        path   = first_line.split()[1] if len(first_line.split()) > 1 else '/'

        print(f'{method} {path} body={len(body)}b')

        cors = b'Access-Control-Allow-Origin: *\r\nAccess-Control-Allow-Methods: POST, GET, OPTIONS\r\nAccess-Control-Allow-Headers: Content-Type\r\n'

        if method == 'OPTIONS':
            conn.sendall(b'HTTP/1.1 200 OK\r\n' + cors + b'Content-Length: 0\r\n\r\n')

        elif method == 'POST' and path == '/print':
            print(f'body: {body[:200]}')
            data = json.loads(body.decode())
            labels = data.get('labels', [])
            sep       = int(data.get('sep', 200))
            font_size = int(data.get('font_size', MAX_FONT))
            print(f'Printing {len(labels)} labels sep={sep} font_size={font_size}')
            print_labels(labels, sep, font_size)
            conn.sendall(b'HTTP/1.1 200 OK\r\n' + cors + b'Content-Length: 2\r\n\r\nOK')

        else:
            conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n' + cors + b'Content-Length: ' + str(len(HTML)).encode() + b'\r\n\r\n' + HTML)

    except Exception as e:
        import traceback
        print('HANDLE ERR:', traceback.format_exc())
        try:
            err = str(e).encode()
            conn.sendall(b'HTTP/1.1 500 ERR\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: ' + str(len(err)).encode() + b'\r\n\r\n' + err)
        except:
            pass
    finally:
        conn.close()

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('0.0.0.0', PORT))
srv.listen(10)
print(f'GaffLabel server on :{PORT}')
while True:
    conn, _ = srv.accept()
    threading.Thread(target=handle, args=(conn,), daemon=True).start()
