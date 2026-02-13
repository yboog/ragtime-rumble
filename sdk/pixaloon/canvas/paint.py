from PySide6 import QtCore, QtGui
from pixaloon.data import get_stair_line, get_interaction_text
from pixaloon.selection import Selection


def paint_canvas_base(painter, document, viewportmapper, rect):
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
            painter.drawImage(rect, image)
        if document.veil_alpha:
            color = QtGui.QColor(QtCore.Qt.white)
            color.setAlpha(document.veil_alpha)
            painter.setBrush(color)
            painter.setPen(color)
            painter.drawRect(rect)


def paint_canvas_selection(painter, document, viewportmapper, selection):
    match selection.tool:
        case Selection.WALL:
            paint_wall(
                painter=painter,
                polygon=document.data['walls'][selection.data],
                viewportmapper=viewportmapper,
                selected=True)
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


def paint_canvas_switchs(painter, document, viewportmapper, left, right):
    for ol in document.data['overlays']:
        p1 = QtCore.QPoint(left, ol['y'])
        p1 = viewportmapper.to_viewport_coords(p1)
        p2 = QtCore.QPoint(right, ol['y'])
        p2 = viewportmapper.to_viewport_coords(p2)
        line = QtCore.QLineF(p1, p2)
        painter.setPen(QtCore.Qt.white)
        painter.drawLine(line)


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


def paint_canvas_walls(painter, document, viewportmapper):
    for rect in document.data['no_go_zones']:
        paint_selected_rect_object(painter, rect, viewportmapper, selected=False)
    for polygon in document.data['walls']:
        paint_wall(painter, polygon, viewportmapper, selected=False)


def paint_selected_rect_object(painter, rect, viewportmapper, selected=False):
    pen = QtGui.QPen(QtCore.Qt.yellow if selected else QtCore.Qt.red)
    pen.setWidth(2 if selected else 1)
    painter.setPen(pen)
    color = QtGui.QColor(QtCore.Qt.red)
    color.setAlpha(125 if selected else 50)
    painter.setBrush(color)
    rect = QtCore.QRect(*rect)
    painter.drawRect(viewportmapper.to_viewport_rect(rect))


def paint_wall(painter, polygon, viewportmapper, selected=False):
    pen = QtGui.QPen(QtCore.Qt.yellow if selected else QtCore.Qt.red)
    pen.setWidth(2 if selected else 1)
    painter.setPen(pen)
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


def paint_canvas_targets(painter, document, viewportmapper):
    for i, origin_dsts in enumerate(document.data['targets']):
        # sel = document.selected_target
        # if sel is not None and i != sel:
        #     continue
        color = QtGui.QColor('#FF00FF')
        painter.setPen(color)
        color.setAlpha(50)
        painter.setBrush(color)
        origin = QtCore.QRect(*origin_dsts['origin'])
        origin = viewportmapper.to_viewport_rect(origin)
        painter.drawRect(origin)
        for dst in origin_dsts['destinations']:
            color = QtGui.QColor('#FFFF00')
            painter.setPen(color)
            color.setAlpha(50)
            painter.setBrush(color)
            dst = QtCore.QRect(*dst)
            dst = viewportmapper.to_viewport_rect(dst)
            painter.drawRect(dst)
            painter.setPen(QtCore.Qt.white)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawLine(origin.center(), dst.center())


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
    for i, interaction in enumerate(document.data['interactions']):
        # selection = document.selected_interaction
        # if i == selection and selection is not None:
        #     painter.setPen(QtCore.Qt.white)
        # else:
        #     painter.setPen(QtCore.Qt.green)
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
    painter.setPen(QtCore.Qt.blue)
    for point in document.data['startups']['unassigned']:
        point = viewportmapper.to_viewport_coords(QtCore.QPointF(*point))
        painter.drawEllipse(point, 4, 4)
    for i, group in enumerate(document.data['startups']['groups']):
        painter.setBrush(QtCore.Qt.green)
        painter.setPen(QtCore.Qt.blue)
        for point in group['assigned']:
            point = viewportmapper.to_viewport_coords(QtCore.QPointF(*point))
            painter.drawEllipse(point, 4, 4)
        directions = 'left', 'up', 'right', 'down'
        points = [
            QtCore.QPointF(*group['popspots'][d]) for d in directions]
        points = [
            viewportmapper.to_viewport_coords(p) for p in points]
        # if i == document.selected_group:
        #     color = QtCore.Qt.white
        # else:
        #     color = QtCore.Qt.magenta
        color = QtCore.Qt.white
        color = QtGui.QColor(color)
        painter.setPen(color)
        color.setAlpha(50)
        painter.setBrush(color)
        polygon = QtGui.QPolygonF(points)
        painter.drawPolygon(polygon)
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.black)
        for direction in directions:
            point = QtCore.QPoint(*group['popspots'][direction])
            painter.drawText(
                viewportmapper.to_viewport_coords(point),
                direction)



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
