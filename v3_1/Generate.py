from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *
from OpenGL.GL import *

MODE_LOOP = 0
MODE_POINT = 1

def determinant(v1, v2, v3, v4):
	return v1*v3-v2*v4

def intersection(p1, p2, p3, p4):
    # Store the values for fast access and easy
    # equations-to-code conversion
    x1 = p1[0]
    x2 = p2[0]
    x3 = p3[0]
    x4 = p4[0]
    y1 = p1[1]
    y2 = p2[1]
    y3 = p3[1]
    y4 = p4[1]
 
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    # If d is zero, there is no intersection
    if d == 0:
     	return None
 
    # Get the x and y
    pre = x1*y2 - y1*x2
    post = x3*y4 - y3*x4
    x = ( pre * (x3 - x4) - (x1 - x2) * post ) / d
    y = ( pre * (y3 - y4) - (y1 - y2) * post ) / d
 
    # Check if the x and y coordinates are within both lines
    if x < min(x1, x2) or x > max(x1, x2) or x < min(x3, x4) or x > max(x3, x4):
     	return None
    if y < min(y1, y2) or y > max(y1, y2) or y < min(y3, y4) or y > max(y3, y4):
     	return None
 
    # Return the point of intersection
    return [x, y]

class DisplayWidget2(QGLWidget):
	def __init__(self, parent):
		QGLWidget.__init__(self, parent)
		self.setMinimumSize(500, 500)

		self.mode = MODE_LOOP

		self.reset()

	def initializeGL(self):
		glClearColor(0.0, 0.0, 0.0, 1.0)
		glClearDepth(1.0)

#        glEnable(GL_POINT_SMOOTH)
#        glEnable(GL_LINE_SMOOTH)

	def paintGL(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# Fill with black
		glClearColor(0.0, 0.0, 0.0, 1.0)

		# Points
		glColor4f(1.0, 0.0, 0.0, 1.0)
		glPointSize(6.0)
		glBegin(GL_POINTS)
		for point in self.points:
			glVertex2f(point[0], point[1])
		for loop in self.loops:
			for point in loop:
				glVertex2f(point[0], point[1])
		for point in self.current_loop:
			glVertex2f(point[0], point[1])
		glEnd()

		# Lines
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glLineWidth(2.0)
		for loop in self.loops:
			glBegin(GL_LINE_LOOP)
			for point in loop:
				glVertex2f(point[0], point[1])
			glEnd()
		glBegin(GL_LINE_STRIP)
		for point in self.current_loop:
			glVertex2f(point[0], point[1])
		glEnd()

	def resizeGL(self, w, h):
		self.w = w
		self.h = h

		glViewport(0, 0, w, h)
		glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)

	def mouseReleaseEvent(self, event):
		x = -1.0 + 2.0 * float(event.x()) / self.w
		y = 1.0 - 2.0 * float(event.y()) / self.h

		if self.mode == MODE_POINT:
			self.points.append([x, y])
			self.update()
			return
		elif self.mode == MODE_LOOP:
			# Finished ?
			if len(self.current_loop) >= 3:
				start_point = self.current_loop[0]
				if (x - start_point[0]) * (x - start_point[0]) + (y - start_point[1]) * (y - start_point[1]) < 1e-3:
					self.loops.append(self.current_loop)
					self.current_loop = []
					self.update()
					return

			# Now we did not end current_loop, so intersection with any other segment is illegal.
			if len(self.current_loop) > 0:
				p0 = self.current_loop[len(self.current_loop) - 1]
				p1 = [x, y]
				for loop in self.loops:
					for i in xrange(len(loop)):
						p2 = loop[i]
						p3 = loop[(i + 1) % len(loop)]
						ii = intersection(p0, p1, p2, p3)
						if ii != None and (p0[0] - ii[0]) * (p0[0] - ii[0]) + (p0[1] - ii[1]) * (p0[1] - ii[1]) > 1e-3:
							msgBox = QMessageBox()
							msgBox.setText("Segments should not intersect")
							msgBox.exec_()
							return
				if len(self.current_loop) > 1:
					for i in xrange(len(self.current_loop) - 1):
						p2 = self.current_loop[i]
						p3 = self.current_loop[(i + 1) % len(self.current_loop)]
						ii = intersection(p0, p1, p2, p3)
						if ii != None and (p0[0] - ii[0]) * (p0[0] - ii[0]) + (p0[1] - ii[1]) * (p0[1] - ii[1]) > 1e-3:
							msgBox = QMessageBox()
							msgBox.setText("Segments should not intersect")
							msgBox.exec_()
							return

			self.current_loop.append([x, y])
			self.update()
			return

	def reset(self):
		self.points = []
		self.loops = []
		self.current_loop = []

	def save(self, filename):
		if len(self.current_loop) > 0:
			msgBox = QMessageBox()
			msgBox.setText("Please finish current loop first")
			msgBox.exec_()
			return

		with open(filename, 'w') as f:
			# Number of points
			num_points = 0
			for loop in self.loops:
				num_points = num_points + len(loop)
			f.write(str(num_points) + ' 2 0 0\n')

			# Points
			i = 0
			for loop in self.loops:
				for point in loop:
					i = i + 1
					f.write(str(i) + ' ' + str(point[0]) + ' ' + str(point[1]) + '\n')

			# Number of segments
			f.write(str(num_points) + ' 0\n')

			# Segments
			i = 1
			for loop in self.loops:
				for j in xrange(len(loop)):
					f.write(str(i + j) + ' ' + str(i + j) + ' ' + str(i + ((j + 1) % len(loop))) + '\n')
				i = i + len(loop)

			# Number of holes
			f.write(str(len(self.points)) + '\n')

			# Holes
			i = 0
			for point in self.points:
				i = i + 1
				f.write(str(i) + ' ' + str(point[0]) + ' ' + str(point[1]) + '\n')

			msgBox = QMessageBox()
			msgBox.setText("Saved successfully.")
			msgBox.exec_()

class Form2(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

		self.buttonReset = QPushButton("Reset")
		self.buttonReset.clicked.connect(self.reset)
		self.buttonLoad = QPushButton("Save to file")
		self.buttonLoad.clicked.connect(self.save)

		groupBox = QGroupBox("Mode")
		self.radioButton1 = QRadioButton("Loop")
		self.radioButton1.clicked.connect(self.setModeLoop)
		self.radioButton1.setChecked(True)
		self.radioButton2 = QRadioButton("Point")
		self.radioButton2.clicked.connect(self.setModePoint)
		groupLayout = QHBoxLayout()
		groupLayout.addWidget(self.radioButton1)
		groupLayout.addWidget(self.radioButton2)
		groupBox.setLayout(groupLayout)

		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(self.buttonReset)
		buttonLayout.addWidget(self.buttonLoad)
		buttonLayout.addWidget(groupBox)

		self.displayWidget = DisplayWidget2(self)
		self.displayWidget.mode = MODE_LOOP

		mainLayout = QVBoxLayout()
		mainLayout.addLayout(buttonLayout)
		mainLayout.addWidget(self.displayWidget)

		self.setLayout(mainLayout)
		self.setWindowTitle("Generate")

	def setModeLoop(self):
		self.displayWidget.mode = MODE_LOOP
	def setModePoint(self):
		self.displayWidget.mode = MODE_POINT

	def reset(self):
		self.displayWidget.reset()
		self.displayWidget.update()

	def save(self):
		file_name = QFileDialog.getSaveFileName(self, "Save Data File", "", "Polygon data files (*.poly)")[0]
		self.displayWidget.save(file_name)

if __name__ == '__main__':
	import sys

	app = QApplication(sys.argv)

	form = Form2()
	form.show()

	sys.exit(app.exec_())
