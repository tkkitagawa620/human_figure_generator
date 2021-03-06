import glob
import random
import cv2


class ScaleDetector():
    def __init__(self, img, vanishingPoint, referencePoint, referenceHeight):
        # Vanishing point
        self.vp = vanishingPoint
        # Y and X cordinates of the reference figure origin
        self.rp = referencePoint
        self.rp_x = referencePoint[0]
        self.rp_y = referencePoint[1]
        self.rp_h = referenceHeight
        # Load image
        self.img = img

    def drawHumanFigureLayout(self, x=None, y=None, h=None, color=None):
        x = x or self.rp_x
        y = y or self.rp_y
        h = h or self.rp_h
        color = color or (0, 255, 0)
        thickness = 4
        fig_w = 40

        top_y = y - h
        top = (x, top_y)
        rp = (x, y)
        _neckline_y = int((y - top_y) * 0.1429 + top_y)

        cv2.line(self.img, rp, top, color, thickness)
        cv2.line(self.img, (x - fig_w, top_y), (x + fig_w, top_y), color, thickness)
        cv2.line(self.img, (x - fig_w, y), (x + fig_w, y), color, thickness)
        cv2.line(self.img, (x - fig_w, _neckline_y), (x + fig_w, _neckline_y), color, thickness)
        return None

    def drawVanishingPoint(self):
        cv2.circle(self.img, tuple(map(int, self.vp)), 5, (0, 255, 0), 4)
        return None

    def drawTargetPoint(self, tp):
        cv2.circle(self.img, tp, 5, (0, 0, 255), 4)

    def getExtendedLine(self, img, pt1, pt2):
        x1, y1 = pt1
        x2, y2 = pt2
        w = img.shape[0]
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        y_0 = b
        y_w = m * w + b
        # print('m: ', m)
        # print('b: ', b)
        # print('y_0: ', y_0)
        # print('y_w: ', y_w)
        # print('extended line cordinates: ', ((0, y_0), (w, y_w)))
        return ((0, y_0), (w, y_w), m, b)

    def findIntersection(self, l1, l2):
        (a, b), (c, d) = l1
        (e, f), (g, h) = l2
        # print(a, b, c, d, e, f, g, h)
        x_deno = (d - b) * (g - e) - (c - a) * (h - f)
        x_nume = (f * g - e * h) * (c - a) - (b * c - a * d) * (g - e)
        y_deno = (d - b) * (g - e) - (c - a) * (h - f)
        y_nume = (f * g - e * h) * (d - b) - (b * c - a * d) * (h - f)
        return (x_nume / x_deno, y_nume / y_deno)

    def drawScaledFigure(self, tp):
        # Init
        tp_x = tp[0]
        tp_y = tp[1]
        tp_h = None
        v_img = self.img.copy()

        # Step 1
        sp1 = self.findIntersection((self.rp, (0, self.rp_y)), (self.vp, tp))
        hl = self.getExtendedLine(v_img, self.rp, (0, self.rp_y))
        cv2.line(v_img, tuple(map(int, hl[0])), tuple(map(int, hl[1])), (255, 0, 0), 2)
        cv2.circle(v_img, tuple(map(int, sp1)), 4, (0, 255, 0), 4)

        # Step 2
        sp2 = (sp1[0], sp1[1] - self.rp_h)
        cv2.circle(v_img, tuple(map(int, sp2)), 4, (0, 255, 0), 4)

        # Step 3
        sl1 = self.getExtendedLine(v_img, self.vp, sp1)
        sl2 = self.getExtendedLine(v_img, self.vp, sp2)
        cv2.line(v_img, tuple(map(int, sl1[0])), tuple(map(int, sl1[1])), (255, 0, 0), 2)
        cv2.line(v_img, tuple(map(int, sl2[0])), tuple(map(int, sl2[1])), (255, 0, 0), 2)

        # Step 4
        tp_top_y = int(sl2[2] * tp_x + sl2[3])
        tp_h = tp_y - tp_top_y
        cv2.circle(v_img, (tp_x, tp_top_y), 4, (0, 255, 0), 4)

        # Visualize the result
        img_paths = glob.glob('./imgs_figures/*.png')
        img = random.choice(img_paths)
        fig = cv2.imread(img, -1)
        self.drawHumanFigure(fig, tp_x, tp_y, tp_h)

        return tp_h

    def drawHumanFigure(self, img, x, y, h):
        alpha_img = img.copy()
        alpha_img_h, alpha_img_w = alpha_img.shape[:2]
        alpha_img_h, alpha_img_w = h, int(alpha_img_w * (h / alpha_img_h))
        alpha_img = cv2.resize(alpha_img, (alpha_img_w, alpha_img_h))

        offset_x = int(x - alpha_img_w / 2)
        offset_y = y - h

        # When offset x position of the figure is negative
        if offset_x < 0:
            visible_width = alpha_img_w + offset_x
            # Cropping image: img[top : bottom, left : right]
            alpha_img = alpha_img[0: alpha_img_h, offset_x: alpha_img_w]
            # Update offset and width
            alpha_img_w = visible_width
            offset_x = 0
        # When offset position of the figure exceeds input image size
        if alpha_img_w + offset_x > self.img.shape[1]:
            visible_width = self.img.shape[1] - offset_x
            # Cropping image: img[top : bottom, left : right]
            alpha_img = alpha_img[0: alpha_img_h, 0: visible_width]
            # Update width
            alpha_img_w = visible_width
        # When offset y position of the figure is negative
        if offset_y < 0:
            visible_height = alpha_img_h + offset_y
            # Crop image: img[top : bottom, left : right]
            alpha_img = alpha_img[alpha_img_h - visible_height: alpha_img_h, 0: alpha_img_w]
            # Update offset and height
            alpha_img_h = visible_height
            offset_y = 0

        self.img = self.merge_images(self.img, alpha_img, offset_x, offset_y)

    def merge_images(self, bg, fg_alpha, s_x, s_y):
        alpha = fg_alpha[:, :, 3]
        alpha = cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR)
        alpha = 0.8 * alpha / 255.0

        fg = fg_alpha[:, :, :3]

        f_h, f_w, _ = fg.shape
        b_h, b_w, _ = bg.shape

        print("f_w:{} f_h:{} b_w:{} b_h:{} s({}, {})".format(f_w, f_h, b_w, b_h, s_x, s_y))

        bg[s_y:f_h + s_y, s_x:f_w + s_x] = (bg[s_y:f_h + s_y, s_x:f_w + s_x] * (1.0 - alpha)).astype('uint8')
        bg[s_y:f_h + s_y, s_x:f_w + s_x] = (bg[s_y:f_h + s_y, s_x:f_w + s_x] + (fg * alpha)).astype('uint8')

        return bg
