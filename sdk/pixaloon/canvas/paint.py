from PySide6 import QtCore, QtGui
from pixaloon.data import get_stair_line, get_interaction_text
from pixaloon.selection import Selection


def paint_canvas_base(painter, document, viewportmapper, rect):
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(25, 25, 25))
        painter.drawRect(rect)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen())
        rect = viewportmapper.to_viewport_rect(QtCore.QRect(0, 0, 640, 360))
        painter.drawRect(rect)
        positions = [bg['position'] for bg in document.data['backgrounds']]
        for pos, image in zip(positions, document.backgrounds):
            img_rect = QtCore.QRect(QtCore.QPoint(*pos), image.size())
            img_rect = viewportmapper.to_viewport_rect(img_rect)
            painter.drawImage(img_rect, image)
        positions = [ol['position'] for ol in document.data['overlays']]
        for pos, image in zip(positions, document.overlays):
            img_rect = QtCore.QRect(QtCore.QPoint(*pos), image.size())
            img_rect = viewportmapper.to_viewport_rect(img_rect)
            painter.drawImage(img_rect, image)
        for prop, image in zip(document.data['props'], document.props):
            x = prop['position'][0] - prop['center'][0]
            y = prop['position'][1] - prop['center'][1]
            point = QtCore.QPoint(x, y)
            img_rect = QtCore.QRect(point, image.size())
            img_rect = viewportmapper.to_viewport_rect(img_rect)
            painter.drawImage(img_rect, image)
        if document.veil_alpha:
            color = QtGui.QColor(QtCore.Qt.white)
            color.setAlpha(document.veil_alpha)
            painter.setBrush(color)
            painter.setPen(color)
            painter.drawRect(rect)


def paint_canvas_selection(painter, document, viewportmapper):
    selection = document.selection
    match selection.tool:
        case Selection.POPSPOT:
            painter.setPen(QtCore.Qt.white)
            painter.setBrush(QtCore.Qt.white)
            for row in document.selection.data:
                x, y = document.data['popspots'][row]
                point = QtCore.QPoint(x, y)
                point = viewportmapper.to_viewport_coords(point)
                painter.drawEllipse(point, 4, 4)
        case Selection.STAIR:
            paint_selected_rect_object(
                painter=painter,
                rect=document.data['stairs'][selection.data]['zone'],
                viewportmapper=viewportmapper,
                selected=True)
        case Selection.WALL:
            paint_wall(
                painter=painter,
                polygon=document.data['walls'][selection.data],
                viewportmapper=viewportmapper,
                selected=True)
        case Selection.PATH:
            path = document.data['paths'][selection.data[0]]
            paint_selected_path(
                painter=painter,
                path=path,
                point_selected_index=selection.data[1],
                viewportmapper=viewportmapper)
        case Selection.NO_GO_ZONE:
            paint_selected_rect_object(
                painter=painter,
                rect=document.data['no_go_zones'][selection.data],
                viewportmapper=viewportmapper,
                selected=True)
        case Selection.INTERACTION:
            zone = (
                document.data['interactions'][selection.data]['zone'] or
                document.data['interactions'][selection.data]['attraction'])
            if zone is None:
                return
            paint_selected_rect_object(
                painter=painter,
                rect=zone,
                viewportmapper=viewportmapper,
                selected=True)
        case Selection.FENCE:
            paint_selected_rect_object(
                painter=painter,
                rect=document.data['fences'][selection.data],
                viewportmapper=viewportmapper,
                selected=True)
        case Selection.SHADOW:
            paint_wall(
                painter=painter,
                polygon=document.data['shadow_zones'][selection.data]['polygon'],
                viewportmapper=viewportmapper,
                selected=True)
        case Selection.TARGET:
            paint_canvas_target(
                painter=painter,
                target=document.data['targets'][selection.data[0]],
                viewportmapper=viewportmapper,
                selected=True,
                selected_destination=selection.data[1])
        case Selection.OVERLAY:
            pos = document.data['overlays'][selection.data]['position']
            image = document.overlays[selection.data]
            img_rect = QtCore.QRect(QtCore.QPoint(*pos), image.size())
            img_rect = viewportmapper.to_viewport_rect(img_rect)
            pen = QtGui.QPen(QtGui.Qt.white)
            pen.setWidth(5)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(img_rect)
            y = document.data['overlays'][selection.data]['y']
            y = viewportmapper.to_viewport_coords(QtCore.QPoint(0, y)).y()
            x = viewportmapper.to_viewport(-1000)
            x2 = viewportmapper.to_viewport(1000)
            painter.drawLine(QtCore.QLine(x, y, x2, y))


def paint_canvas_switchs(painter, document, viewportmapper, left, right):
    for ol in document.data['overlays']:
        p1 = QtCore.QPoint(left, ol['y'])
        p1 = viewportmapper.to_viewport_coords(p1)
        p2 = QtCore.QPoint(right, ol['y'])
        p2 = viewportmapper.to_viewport_coords(p2)
        line = QtCore.QLineF(p1, p2)
        painter.setPen(QtCore.Qt.white)
        painter.drawLine(line)


def paint_scores(painter, document, viewportmapper):
    position = document.data['score']['ol']['position']
    image = document.scores['overlay']
    rect = QtCore.QRect(QtCore.QPoint(*position), image.size())
    rect = viewportmapper.to_viewport_rect(rect)
    painter.drawImage(rect, image)
    for i in range(1, 5):
        p = f'player{i}'
        position = document.data['score'][p]['life']['position']
        image = document.scores[p]['life']
        rect = QtCore.QRect(QtCore.QPoint(*position), image.size())
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawImage(rect, image)
        position = document.data['score'][p]['bullet']['position']
        image = document.scores[p]['bullet']
        rect = QtCore.QRect(QtCore.QPoint(*position), image.size())
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawImage(rect, image)
        position = document.data['score'][p]['coins_position']
        image = document.scores['coin-stack']
        rect = QtCore.QRect(QtCore.QPoint(*position), image.size())
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawImage(rect, image)


def paint_canvas_popspots(painter, document, viewportmapper):
    painter.setPen(QtCore.Qt.yellow)
    painter.setBrush(QtCore.Qt.yellow)
    for x, y in document.data['popspots']:
        point = QtCore.QPoint(x, y)
        point = viewportmapper.to_viewport_coords(point)
        painter.drawEllipse(point, 2, 2)


def paint_canvas_props(painter, document, viewportmapper):
    for prop in document.data['props']:
        x = prop['position'][0] + prop['center'][0]
        y = prop['position'][1] + prop['center'][1]
        width = prop['position'][0] + prop['box'][0]
        height = prop['position'][1] + prop['box'][1]
        color = QtGui.QColor('pink')
        painter.setPen(color)
        color.setAlpha(50)
        painter.setBrush(color)
        rect = QtCore.QRect(x, y, width, height)
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawRect(rect)
        painter.setPen(QtCore.Qt.white)
        painter.setBrush(QtCore.Qt.white)
        painter.drawEllipse(rect.left(), rect.top(), 2, 2)


def paint_canvas_shadow_zones(painter, document, viewportmapper):
    for data in document.data['shadow_zones']:
        color = QtGui.QColor(*data['color'])
        paint_wall(painter, data['polygon'], viewportmapper, color)


def paint_canvas_walls(painter, document, viewportmapper):
    for rect in document.data['no_go_zones']:
        paint_selected_rect_object(painter, rect, viewportmapper, selected=False)
    for polygon in document.data['walls']:
        paint_wall(painter, polygon, viewportmapper, color=None, selected=False)


def paint_selected_rect_object(painter, rect, viewportmapper, selected=False):
    pen = QtGui.QPen(QtCore.Qt.yellow if selected else QtCore.Qt.red)
    pen.setWidth(2 if selected else 1)
    painter.setPen(pen)
    color = QtGui.QColor(QtCore.Qt.red)
    color.setAlpha(125 if selected else 50)
    painter.setBrush(color)
    rect = QtCore.QRect(*rect)
    painter.drawRect(viewportmapper.to_viewport_rect(rect))


def paint_wall(painter, polygon, viewportmapper, color=None, selected=False):
    pen = QtGui.QPen(QtCore.Qt.yellow if selected else QtCore.Qt.red)
    pen.setWidth(2 if selected else 1)
    painter.setPen(pen)
    if not color:
        color = QtGui.QColor(QtCore.Qt.red)
        color.setAlpha(125 if selected else 50)
    painter.setBrush(color)
    polygon = QtGui.QPolygonF([
        viewportmapper.to_viewport_coords(QtCore.QPoint(*p))
        for p in polygon])
    painter.drawPolygon(polygon)


def paint_canvas_stairs(painter, document, viewportmapper):
    for stair in document.data['stairs']:
        color = QtGui.QColor("#DEABDE")
        painter.setPen(color)
        color.setAlpha(50)
        painter.setBrush(color)
        rect = QtCore.QRect(*stair['zone'])
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawRect(rect)
        painter.setPen(QtCore.Qt.white)
        line = get_stair_line(rect, stair['inclination'])
        painter.drawLine(line)


def paint_canvas_target(
        painter,
        target,
        viewportmapper,
        selected=False,
        selected_destination=False):
    color = QtGui.QColor('#FF00FF' if not selected else 'cyan')
    painter.setPen(color)
    color.setAlpha(25 if not selected else 255)
    painter.setBrush(color)
    origin = QtCore.QRect(*target['origin'])
    origin = viewportmapper.to_viewport_rect(origin)
    painter.drawRect(origin)
    lines = []
    for i, dst in enumerate(target['destinations']):
        color = (
            '#FFFF00' if
            not selected else 'white' if
            not selected_destination == i else 'red')
        color = QtGui.QColor(color)
        pen = QtGui.QPen(color)
        pen.setWidth(4 if selected_destination == i and selected else 1)
        painter.setPen(pen)
        color.setAlpha(25 if not selected else 120)
        painter.setBrush(color)
        dst = QtCore.QRect(*dst)
        dst = viewportmapper.to_viewport_rect(dst)
        painter.drawRect(dst)
        lines.append(QtCore.QLineF(origin.center(), dst.center()))
    pen = QtGui.QPen(QtCore.Qt.white if not selected else QtCore.Qt.black)
    pen.setWidth(1 if not selected else 3)
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.NoBrush)
    for line in lines:
        painter.drawLine(line)


def paint_canvas_fences(painter, document, viewportmapper):
    color = QtGui.QColor(QtCore.Qt.cyan)
    painter.setPen(color)
    color.setAlpha(50)
    painter.setBrush(color)
    for fence in document.data['fences']:
        rect = QtCore.QRect(*fence)
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawRect(rect)


def paint_canvas_interactions(painter, document, viewportmapper):
    color = QtGui.QColor(QtCore.Qt.green)
    color.setAlpha(50)
    painter.setBrush(color)
    align = QtCore.Qt.AlignCenter
    painter.setPen(QtCore.Qt.white)
    for interaction in document.data['interactions']:
        color.setAlpha(50)
        painter.setBrush(color)
        painter.setBrush(color)
        rect = QtCore.QRect(*interaction['zone'])
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawRect(rect)
        text = get_interaction_text(interaction)
        painter.drawText(rect, align, text)
        color.setAlpha(25)
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.NoPen)
        rect = QtCore.QRect(*interaction['attraction'])
        rect = viewportmapper.to_viewport_rect(rect)
        painter.drawRect(rect)
        painter.setPen(QtCore.Qt.white)
        painter.setBrush(QtCore.Qt.white)
        if None not in interaction['target']:
            point = QtCore.QPoint(*interaction['target'])
            point = viewportmapper.to_viewport_coords(point)
            painter.drawEllipse(point, 2, 2)
        elif interaction['target'][0] is None:
            y = interaction['target'][1]
            p1 = QtCore.QPoint(interaction['zone'][0], y)
            p1 = viewportmapper.to_viewport_coords(p1)
            x = interaction['zone'][0] + interaction['zone'][2]
            p2 = QtCore.QPoint(x, y)
            p2 = viewportmapper.to_viewport_coords(p2)
            painter.drawLine(p1, p2)
        elif interaction['target'][1] is None:
            x = interaction['target'][0]
            p1 = QtCore.QPoint(x, interaction['zone'][1])
            p1 = viewportmapper.to_viewport_coords(p1)
            y = interaction['zone'][1] + interaction['zone'][3]
            p2 = QtCore.QPoint(x, y)
            p2 = viewportmapper.to_viewport_coords(p2)
            painter.drawLine(p1, p2)


def paint_canvas_startups(painter, document, viewportmapper):
    painter.setBrush(QtCore.Qt.green)
    painter.setPen(QtCore.Qt.black)
    font = QtGui.QFont()
    font.setBold(True)
    font.setFamily('terminal')
    font.setPointSize(12)
    painter.setFont(font)
    last_point = None
    for i, point in enumerate(document.data['startups']['unassigned']):
        point = viewportmapper.to_viewport_coords(QtCore.QPointF(*point))
        painter.drawEllipse(point, 4, 4)
        painter.drawText(point + QtCore.QPointF(5, 2), f'{i + 1}')
        if last_point:
            painter.drawLine(point, last_point)
        last_point = point
    for i, group in enumerate(document.data['startups']['groups']):
        # startup groups
        directions = 'left', 'up', 'right', 'down'
        points = [
            QtCore.QPointF(*group['popspots'][d]) for d in directions]
        points = [
            viewportmapper.to_viewport_coords(p) for p in points]
        color = QtCore.Qt.white
        color = QtGui.QColor(color)
        painter.setPen(color)
        color.setAlpha(50)
        painter.setBrush(color)
        polygon = QtGui.QPolygonF(points)
        painter.drawPolygon(polygon)
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.black)
        center = QtCore.QPointF()
        for p in points:
            center += p
        center /= 4
        for direction in directions:
            point = QtCore.QPoint(*group['popspots'][direction])
            painter.drawText(
                viewportmapper.to_viewport_coords(point),
                direction)

        # gamepad placement
        painter.setBrush(QtCore.Qt.green)
        painter.setPen(QtCore.Qt.blue)
        last_point = None
        closest_point = None
        for j, point in enumerate(group['assigned']):
            point = viewportmapper.to_viewport_coords(QtCore.QPointF(*point))
            painter.drawEllipse(point, 4, 4)
            painter.drawText(point + QtCore.QPointF(5, 2), f'{j + 1}')
            if not last_point:
                p = point + QtCore.QPointF(25, 2)
                painter.drawText(p, f'Player {i + 1}')
            else:
                painter.drawLine(point, last_point)
            last_point = point
            if closest_point is None:
                closest_point = point
                continue
            closest_point = (
                point if QtCore.QLineF(closest_point, center).length() >
                QtCore.QLineF(point, center).length() else closest_point)
        painter.drawLine(center, closest_point)


def paint_canvas_paths(painter, document, viewportmapper):
    painter.setBrush(QtCore.Qt.NoBrush)
    for path in document.data['paths']:
        if path['hard']:
            pen = QtGui.QPen(QtCore.Qt.blue)
            pen.setWidth(2)
            pen.setStyle(QtCore.Qt.SolidLine)
        else:
            pen = QtGui.QPen(QtCore.Qt.cyan)
            pen.setStyle(QtCore.Qt.DashDotDotLine)
        painter.setPen(pen)
        points = [
            viewportmapper.to_viewport_coords(QtCore.QPoint(*p))
            for p in path['points']]
        start = None
        for end in points:
            if start is None:
                start = end
                continue
            painter.drawLine(start, end)
            start = end
        painter.setPen(QtCore.Qt.green)
        painter.drawEllipse(points[0], 2, 2)
        painter.setPen(QtCore.Qt.red)
        painter.drawEllipse(points[-1], 1, 1)


def paint_selected_path(painter, path, point_selected_index, viewportmapper):
        pen = QtGui.QPen(QtCore.Qt.white)
        pen.setWidth(4)
        pen.setStyle(QtCore.Qt.SolidLine)
        painter.setPen(pen)
        points = [
            viewportmapper.to_viewport_coords(QtCore.QPoint(*p))
            for p in path['points']]

        r = QtCore.QRectF(-10, -8, 20, 10)
        ref_rect = viewportmapper.to_viewport_rect(r)
        lines = []
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(150, 150, 30))
        start = None
        for end in points:
            rect = QtCore.QRectF(ref_rect)
            rect.moveCenter(end)
            painter.drawRect(rect)
            if start is None:
                last_rect = rect
                start = end
                continue
            lines.append(QtCore.QLineF(start, end))
            start = end
            if not path['hard']:
                continue
            ppoints = [
                rect.topLeft(), rect.bottomLeft(),
                last_rect.bottomLeft(), last_rect.topLeft()]
            painter.drawPolygon(QtGui.QPolygonF(ppoints))
            ppoints = [
                rect.topLeft(), rect.topRight(),
                last_rect.topRight(), last_rect.topLeft()]
            painter.drawPolygon(QtGui.QPolygonF(ppoints))
            ppoints = [
                rect.topRight(), rect.topLeft(),
                last_rect.topLeft(), last_rect.topRight()]
            painter.drawPolygon(QtGui.QPolygonF(ppoints))
            ppoints = [
                rect.bottomRight(), rect.bottomLeft(),
                last_rect.bottomLeft(), last_rect.bottomRight()]
            painter.drawPolygon(QtGui.QPolygonF(ppoints))
            last_rect = rect

        pen = QtGui.QPen(QtCore.Qt.white)
        pen.setWidth(2)
        painter.setPen(pen)
        for line in lines:
            painter.drawLine(line)

        if point_selected_index is not None:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtCore.Qt.yellow)
            painter.drawEllipse(points[point_selected_index], 5, 5)