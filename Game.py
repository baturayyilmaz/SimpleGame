import sys
from random import random, randrange

import glm
import numpy as np
from OpenGL import GL as gl, GLUT as glut
from OpenGL.GL import shaders
from Utilities2 import *
import time
from math import cos, sin


class Opponent:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0), scale=glm.vec3(1.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale
        self.color = glm.vec3(1, 0, 0)

        self.front = glm.vec3(0.0, 0.0, 1.0)
        self.rotation = glm.quat(glm.vec3(0.0))

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = transformation * glm.mat4_cast(self.rotation)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def move(self, direction, velocity):
        self.position += direction * velocity

    def turnBack(self):
        self.rotation = glm.quat(glm.vec3(0.0, glm.radians(180), 0.0))
        self.front = glm.vec3(0.0, 0.0, 1.0)

    def turnFront(self):
        self.rotation = glm.quat(glm.vec3(0.0, glm.radians(0), 0.0))
        self.front = glm.vec3(0.0, 0.0, -1.0)

    def shoot(self,
              destination):  # position will be point it will be initiated. destination will be a point it will reach
        global Active_Bullets
        pos = glm.vec3(self.position.x, self.position.y, self.position.z + 1)
        bullet = Bullet(custom_sphere_object, position=pos, scale=glm.vec3(0.05))
        movement_vector = destination - bullet.position
        bullet.destination = bullet.position + movement_vector
        Active_Bullets_Opponent.append(bullet)

    def get_AABB(self):
        dimensions = self.obj_data.dimensions
        transformation = self.get_transformation()

        # Get 8 corners of the AABB
        points = []
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    points.append(glm.vec3(dimensions[0][x], dimensions[1][y], dimensions[2][z]))

        # Transform each corner
        for i in range(len(points)):
            points[i] = tuple((transformation * glm.vec4(points[i], 1.0)).xyz)

        # Use utilities get_dimensions to find the new AABB of the transformed AABB
        return get_dimensions(points)

    def check_AABB_collision(self, AABB):
        self_AABB = self.get_AABB()

        return (self_AABB[0][0] <= AABB[0][1] and self_AABB[0][1] >= AABB[0][0]) \
               and (self_AABB[1][0] <= AABB[1][1] and self_AABB[1][1] >= AABB[1][0]) \
               and (self_AABB[2][0] <= AABB[2][1] and self_AABB[2][1] >= AABB[2][0])

    def generateShadow(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)
        gl.glUniformMatrix4fv(transformation_location2, 1, False, glm.value_ptr(self.get_transformation()))
        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        # Gving the color attribute to fragment shader
        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "color"), 1,
                        glm.value_ptr(self.color))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)


class Player:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0), scale=glm.vec3(1.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale
        self.color = glm.vec3(0, 0, 1)

        # self.front = glm.vec3(self.position.x, self.position.z, (self.position.y - 1)) - self.position
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.rotation = glm.quat(glm.vec3(0.0))

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = transformation * glm.mat4_cast(self.rotation)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def move(self, direction, velocity):
        self.position += direction * velocity

    def turnBack(self):
        # self.rotation = glm.quat(glm.vec3(0.0, glm.radians(180), 0.0))
        global turn_to
        turn_to = glm.quat(glm.vec3(0.0, glm.radians(180.0), 0.0))
        self.front = glm.vec3(0.0, 0.0, 1.0)

    def turnFront(self):
        # self.rotation = glm.quat(glm.vec3(0.0, glm.radians(0), 0.0))
        global turn_to
        turn_to = glm.quat(glm.vec3(0.0, glm.radians(0.0), 0.0))
        self.front = glm.vec3(0.0, 0.0, -1.0)

    def shoot(self,
              destination):  # position will be point it will be initiated. destination will be a point it will reach
        global Active_Bullets
        # print(self.position)
        # print(glm.vec3(0.0, 0.0, 0.0))
        pos = glm.vec3(self.position.x, self.position.y, self.position.z - 1)
        bullet = Bullet(custom_sphere_object, position=pos, scale=glm.vec3(0.05))
        movement_vector = destination - bullet.position
        bullet.destination = bullet.position + movement_vector
        # print(bullet.destination)
        Active_Bullets.append(bullet)

    def get_AABB(self):
        dimensions = self.obj_data.dimensions
        transformation = self.get_transformation()

        # Get 8 corners of the AABB
        points = []
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    points.append(glm.vec3(dimensions[0][x], dimensions[1][y], dimensions[2][z]))

        # Transform each corner
        for i in range(len(points)):
            points[i] = tuple((transformation * glm.vec4(points[i], 1.0)).xyz)

        # Use utilities get_dimensions to find the new AABB of the transformed AABB
        return get_dimensions(points)

    def check_AABB_collision(self, AABB):
        self_AABB = self.get_AABB()

        return (self_AABB[0][0] <= AABB[0][1] and self_AABB[0][1] >= AABB[0][0]) \
               and (self_AABB[1][0] <= AABB[1][1] and self_AABB[1][1] >= AABB[1][0]) \
               and (self_AABB[2][0] <= AABB[2][1] and self_AABB[2][1] >= AABB[2][0])

    def generateShadow(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)
        gl.glUniformMatrix4fv(transformation_location2, 1, False, glm.value_ptr(self.get_transformation()))
        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "color"), 1, glm.value_ptr(self.color))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)


class Spectator:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0), scale=glm.vec3(1.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale
        self.color = glm.vec3(0, 1, 0)

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def shoot(self,
              destination):  # position will be point it will be initiated. destination will be a point it will reach
        global Active_Bullets
        pos = glm.vec3(self.position.x + 0.5, self.position.y, self.position.z)
        bullet = Bullet(custom_sphere_object, position=pos, scale=glm.vec3(0.05))
        movement_vector = destination - bullet.position
        bullet.destination = bullet.position + movement_vector
        Active_Bullets_Referee.append(bullet)

    def generateShadow(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)
        gl.glUniformMatrix4fv(transformation_location2, 1, False, glm.value_ptr(self.get_transformation()))
        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "color"), 1, glm.value_ptr(self.color))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

FreeCamera = False
class Camera:
    def __init__(self, parent: 'GameObject' = None, position=glm.vec3(0.0, 0.0, 0.0), target=glm.vec3(0.0, 0.0, 1.0),
                 up=glm.vec3(0.0, 1.0, 0.0)):
        self.position = position
        self.target = target
        self.up = up
        self.front = target - position
        self.right = glm.cross(self.front, self.up)

        self.parent = parent
        # if parent none mı diye bakılabilir.
        self.vectorToParent = self.parent.position - self.position

    def get_view(self):
        global FreeCamera
        if self.parent == None or FreeCamera == True:
            return glm.lookAt(self.position, self.target, self.up)
        else:
            # pos = self.parent.position + -self.vectorToParent
            v = glm.vec4(self.position, 1.0)
            posMat = self.parent.get_transformation() * v
            pos = glm.vec3(posMat.x, posMat.y, posMat.z)
            return glm.lookAt(pos, self.target, self.up)

    def setTarget(self, target):
        self.target = target
        self.front = self.target - self.position
        self.right = glm.cross(self.front, self.up)

    # def update_vectors(self):

    def moveCamera(self, direction, velocity):
        if direction == "FORWARD":
            self.position += self.front * velocity
            self.target = self.position + self.front
        if direction == "BACKWARD":
            self.position -= self.front * velocity
            self.target = self.position + self.front
        if direction == "LEFT":
            self.position -= self.right * velocity
            self.target = self.position + self.front
        if direction == "RIGHT":
            self.position += self.right * velocity
            self.target = self.position + self.front


class Ground:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0), scale=glm.vec3(1.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale
        self.color = glm.vec3(0.8, 0.4, 0)

        self.rotation = glm.quat(glm.vec3(glm.radians(90), 0.0, 0.0))

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = transformation * glm.mat4_cast(self.rotation)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def get_AABB(self):
        dimensions = self.obj_data.dimensions
        transformation = self.get_transformation()

        # Get 8 corners of the AABB
        points = []
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    points.append(glm.vec3(dimensions[0][x], dimensions[1][y], dimensions[2][z]))

        # Transform each corner
        for i in range(len(points)):
            points[i] = tuple((transformation * glm.vec4(points[i], 1.0)).xyz)

        # Use utilities get_dimensions to find the new AABB of the transformed AABB
        return get_dimensions(points)

    def check_AABB_collision(self, AABB):
        self_AABB = self.get_AABB()

        return (self_AABB[0][0] <= AABB[0][1] and self_AABB[0][1] >= AABB[0][0]) \
               and (self_AABB[1][0] <= AABB[1][1] and self_AABB[1][1] >= AABB[1][0]) \
               and (self_AABB[2][0] <= AABB[2][1] and self_AABB[2][1] >= AABB[2][0])

    def generateShadow(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)
        gl.glUniformMatrix4fv(transformation_location2, 1, False, glm.value_ptr(self.get_transformation()))
        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "color"), 1, glm.value_ptr(self.color))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)


class Bullet:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0, 0.0, -3.0), scale=glm.vec3(1.0),
                 destination=glm.vec3(0.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale
        self.destination = destination
        self.color = glm.vec3(0.0, 0.0, 0.0)

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def get_AABB(self):
        dimensions = self.obj_data.dimensions
        transformation = self.get_transformation()

        # Get 8 corners of the AABB
        points = []
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    points.append(glm.vec3(dimensions[0][x], dimensions[1][y], dimensions[2][z]))

        # Transform each corner
        for i in range(len(points)):
            points[i] = tuple((transformation * glm.vec4(points[i], 1.0)).xyz)

        # Use utilities get_dimensions to find the new AABB of the transformed AABB
        return get_dimensions(points)

    def check_AABB_collision(self, AABB):
        self_AABB = self.get_AABB()

        return (self_AABB[0][0] <= AABB[0][1] and self_AABB[0][1] >= AABB[0][0]) \
               and (self_AABB[1][0] <= AABB[1][1] and self_AABB[1][1] >= AABB[1][0]) \
               and (self_AABB[2][0] <= AABB[2][1] and self_AABB[2][1] >= AABB[2][0])

    def generateShadow(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)
        gl.glUniformMatrix4fv(transformation_location2, 1, False, glm.value_ptr(self.get_transformation()))
        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "color"), 1, glm.value_ptr(self.color))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)


class Haystack:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0), scale=glm.vec3(1.0),
                 gravity=glm.vec3(0.0, -3.0, 0.0), velocity=glm.vec3(0.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale
        # self.color = glm.vec3(0.7, 0.42, 0.31)

        self.gravity = gravity
        self.velocity = velocity
        self.rotation = glm.quat(glm.vec3(0.0))
        self.wind = glm.vec3(1.0, 0.0, -1.0)

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = transformation * glm.mat4_cast(self.rotation)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def get_AABB(self):
        dimensions = self.obj_data.dimensions
        transformation = self.get_transformation()

        # Get 8 corners of the AABB
        points = []
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    points.append(glm.vec3(dimensions[0][x], dimensions[1][y], dimensions[2][z]))

        # Transform each corner
        for i in range(len(points)):
            points[i] = tuple((transformation * glm.vec4(points[i], 1.0)).xyz)

        # Use utilities get_dimensions to find the new AABB of the transformed AABB
        return get_dimensions(points)

    def check_AABB_collision(self, AABB):
        self_AABB = self.get_AABB()

        return (self_AABB[0][0] <= AABB[0][1] and self_AABB[0][1] >= AABB[0][0]) \
               and (self_AABB[1][0] <= AABB[1][1] and self_AABB[1][1] >= AABB[1][0]) \
               and (self_AABB[2][0] <= AABB[2][1] and self_AABB[2][1] >= AABB[2][0])

    def generateShadow(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)
        gl.glUniformMatrix4fv(transformation_location2, 1, False, glm.value_ptr(self.get_transformation()))
        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        # gl.glUniform3fv(gl.glGetUniformLocation(shader_program, "color"), 1, glm.value_ptr(self.color))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)


class Crate:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0), scale=glm.vec3(1.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def generateShadow(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)
        gl.glUniformMatrix4fv(transformation_location2, 1, False, glm.value_ptr(self.get_transformation()))
        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)


class GameOver:
    def __init__(self, obj_data: BoundObjData, position=glm.vec3(0.0), scale=glm.vec3(1.0)):
        self.obj_data = obj_data
        self.position = position
        self.scale = scale

        self.rotation = glm.quat(glm.vec3(0.0, 0.0, 0.0))

    def get_transformation(self):
        transformation = glm.mat4x4()
        transformation = glm.translate(transformation, self.position)
        transformation = transformation * glm.mat4_cast(self.rotation)
        transformation = glm.scale(transformation, self.scale)
        return transformation

    def draw(self):
        # Set the vao
        gl.glBindVertexArray(self.obj_data.vao)

        # Set material uniforms
        gl.glUniform3fv(ambient_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ka))
        gl.glUniform3fv(diffuse_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Kd))
        gl.glUniform3fv(specular_color_location, 1, glm.value_ptr(self.obj_data.meshes[0].material.Ks))
        gl.glUniform1fv(shininess_location, 1, self.obj_data.meshes[0].material.Ns)

        # Set material textures
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Ka)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj_data.meshes[0].material.map_Kd)

        # Set the transform uniform to self.transform
        gl.glUniformMatrix4fv(transformation_location, 1, False, glm.value_ptr(self.get_transformation()))

        # Draw the mesh with an element buffer.
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.obj_data.meshes[0].element_array_buffer)
        # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
        gl.glDrawElements(gl.GL_TRIANGLES, self.obj_data.meshes[0].element_count, gl.GL_UNSIGNED_INT, None)


# Initialize GLUT ------------------------------------------------------------------|
glut.glutInit()
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)

# Create a window
screen_size = glm.vec2(512, 512)
glut.glutCreateWindow("ENDGAME")
glut.glutReshapeWindow(int(screen_size.x), int(screen_size.y))

time_passed = 0
one_shot = True
turn_to = glm.quat()
#delay = 0

Active_Bullets = []
Active_Bullets_Opponent = []
Active_Bullets_Referee = []

GameEnd = False
Won = False


# Set callback functions
def display():
    global GameEnd
    global Won
    global delay
    if GameEnd == False:
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, depthMapFBO)
        gl.glViewport(0, 0, SHADOW_WIDTH, SHADOW_HEIGHT)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

        gl.glUseProgram(simpleDepthShader)
        gl.glUniformMatrix4fv(lightSpaceMatrix_location, 1, False, glm.value_ptr(lightSpaceMatrix))
        player.generateShadow()
        opponent.generateShadow()
        spectator1.generateShadow()
        spectator2.generateShadow()
        crate1.generateShadow()
        crate2.generateShadow()
        haystack.generateShadow()
        for bullet in Active_Bullets:
            bullet.generateShadow()

        for bullet in Active_Bullets_Opponent:
            bullet.generateShadow()

        for bullet in Active_Bullets_Referee:
            bullet.generateShadow()
        ground.generateShadow()

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(0, 0, int(screen_size.x), int(screen_size.y))

        gl.glClearColor(0.2, 0.6, 1, 1)  # giving the color of the sky
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glUseProgram(shader_program)

        gl.glActiveTexture(gl.GL_TEXTURE2)
        # Bind mask to the GL_TEXTURE_2D and GL_TEXTURE2
        gl.glBindTexture(gl.GL_TEXTURE_2D, depthMap)

        # # Update time
        global time_passed
        delta_time = time.perf_counter() - time_passed
        time_passed += delta_time
        #
        # # Updates
        player.rotation = glm.mix(player.rotation, turn_to, 0.05)  # FOR SMOOTH TURN ANIMATION FOR PLAYER
        haystack.rotation = glm.quat(
            glm.vec3(glm.radians(time.perf_counter() * 180.0), 0.0, -glm.radians(time.perf_counter() * 180.0)))

        gl.glUniformMatrix4fv(lightSpaceMatrix_location_Main, 1, False, glm.value_ptr(lightSpaceMatrix))
        gl.glUniformMatrix4fv(projection_location, 1, False, glm.value_ptr(perspective_projection))
        gl.glUniformMatrix4fv(view_location, 1, False, glm.value_ptr(camera.get_view()))
        gl.glUniform3fv(camera_position_location, 1, glm.value_ptr(camera.position))

        # Collision checking
        # Demonstrate some collision checking
        for bullet in Active_Bullets:
            for collision_tester in collision_testers:
                if bullet.check_AABB_collision(collision_tester.get_AABB()):
                    collision_tester.color = glm.vec3(1.0, 1.0, 0.0)
                    Active_Bullets.remove(bullet)
                    GameEnd = True
                    Won = True
                    # if collision_tester = palyer in here, it means that player shot himself. It is not checked for now.

        for bullet in Active_Bullets_Opponent:
            for collision_tester in collision_testers:
                if bullet.check_AABB_collision(collision_tester.get_AABB()):
                    collision_tester.color = glm.vec3(1.0, 1.0, 0.0)
                    Active_Bullets_Opponent.remove(bullet)
                    GameEnd = True
                    Won = False

        for bullet in Active_Bullets_Referee:
            for collision_tester in collision_testers:
                if bullet.check_AABB_collision(collision_tester.get_AABB()):
                    collision_tester.color = glm.vec3(1.0, 1.0, 0.0)
                    Active_Bullets_Referee.remove(bullet)
                    GameEnd = True
                    Won = False

        if haystack.check_AABB_collision(ground.get_AABB()):
            haystack.velocity = glm.vec3(0.0, 1.5, 0.0)

        haystack.velocity += haystack.gravity * delta_time
        haystack.position += haystack.velocity * delta_time
        haystack.position += haystack.wind * delta_time

        opponent.draw()
        player.draw()
        spectator2.draw()
        spectator1.draw()
        ground.draw()
        haystack.draw()
        crate1.draw()
        crate2.draw()

        for bullet in Active_Bullets:
            bullet.draw()
            move_vec = bullet.destination - bullet.position
            bullet.position += move_vec * 0.01
            reached_destination = glm.vec3(bullet.destination.x, bullet.destination.y, bullet.destination.z + 1.0)
            # print(bullet.position.z)
            # print(reached_destination.z)
            if bullet.position.z <= reached_destination.z:
                # print("asd")
                Active_Bullets.remove(bullet)

        for bullet in Active_Bullets_Opponent:
            bullet.draw()
            move_vec = bullet.destination - bullet.position
            bullet.position += move_vec * 0.01
            reached_destination = glm.vec3(bullet.destination.x, bullet.destination.y, bullet.destination.z - 1)
            if bullet.position.z >= reached_destination.z:
                Active_Bullets_Opponent.remove(bullet)

        for bullet in Active_Bullets_Referee:
            bullet.draw()
            move_vec = bullet.destination - bullet.position
            bullet.position += move_vec * 0.025
            # reached_destination = glm.vec3(bullet.destination.x - 1, bullet.destination.y, bullet.destination.z)
            # if bullet.position.z >= reached_destination.z:
            #     Active_Bullets_Referee.remove(bullet)

        global number_Of_Step_Taken
        if number_Of_Step_Taken == 10:
            num = randrange(600)
            # print(num)
            if num == 0:
                x = randrange(-2, 2)
                y = randrange(0, 2)
                pos = glm.vec3(x, y, player.position.z + 1)
                opponent.shoot(pos)

        if number_Of_Step_Taken > 10:
            global one_shot
            if one_shot:
                spectator2.shoot(player.position)
                one_shot = False


    else:
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        player.rotation = glm.quat(glm.vec3(0.0, glm.radians(0.0), 0.0))
        player.position = glm.vec3(player.position.x, player.position.y, player.position.z + 3)
        gamelost.position = player.position
        gamewon.position = player.position

        orthognonal_projection = glm.ortho(-10.0, 10.0, -10.0, 10.0, 0.1, 50)

        gl.glUseProgram(shader_program)
        # gl.glUniformMatrix4fv(lightSpaceMatrix_location_Main, 1, False, glm.value_ptr(lightSpaceMatrix))
        gl.glUniformMatrix4fv(projection_location, 1, False, glm.value_ptr(orthognonal_projection))
        gl.glUniformMatrix4fv(view_location, 1, False, glm.value_ptr(camera.get_view()))
        gl.glUniform3fv(camera_position_location, 1, glm.value_ptr(camera.position))
        if Won:
            gamewon.draw()
        else:
            gamelost.draw()

    # Swap the buffer we just drew on with the one showing on the screen
    glut.glutSwapBuffers()


glut.glutDisplayFunc(display)
glut.glutIdleFunc(display)


def resize(width, height):
    gl.glViewport(0, 0, width, height)
    screen_size.x = width
    screen_size.y = height
    global perspective_projection
    perspective_projection = glm.perspective(glm.radians(45.0), screen_size.x / screen_size.y, 0.1, 100.0)


glut.glutReshapeFunc(resize)

number_Of_Step_Taken = 0

SuperShot = False

def keyboard_input(key, x, y):
    if key == b'\x1b':
        sys.exit()

    global number_Of_Step_Taken
    global FreeCamera
    if key == b'w':
        if FreeCamera:
            camera.moveCamera("FORWARD", 0.05)
        else:
            player.move(player.front, 0.5)
            opponent.move(-opponent.front, 0.5)

            number_Of_Step_Taken += 1

    if key == b's':
        if FreeCamera:
            camera.moveCamera("BACKWARD", 0.05)
        else:
            player.move(-player.front, 0.5)
            opponent.move(opponent.front, 0.5)

    if key == b'a':
        if FreeCamera:
            camera.moveCamera("LEFT", 0.05)
        # turn_speed = glm.quat(glm.vec3(0.0, glm.radians(180.0), 0.0))
        else:
            player.turnBack()
            opponent.turnBack()

    if key == b'd':
        if FreeCamera:
            camera.moveCamera("RIGHT", 0.05)
        # turn_speed = glm.quat(glm.vec3(0.0, glm.radians(-180.0), 0.0))
        else:
            player.turnFront()
            opponent.turnFront()

            if number_Of_Step_Taken < 10:
                spectator2.shoot(player.position)
    global SuperShot
    if key == b'u':
        SuperShot = True

    if key == b'f':
        FreeCamera = True


glut.glutKeyboardFunc(keyboard_input)


# Callback for any mouse button input
def mouse_button_input(button, state, x, y):  # button = 0 -> left click
    global FreeCamera
    if button == 0 and state == 0:  # if left click is pressed
        if FreeCamera == False:
            mouse_pos = glm.vec2(x, y)
            normalized_mouse_pos = ((mouse_pos / screen_size) * 2.0 - 1.0) * 10
            normalized_mouse_pos.y *= -1.0
            world2screen_transformation = perspective_projection * camera.get_view()
            screen2world_transformation = glm.inverse(world2screen_transformation)
            # Because I want to transform the mouse position to a plane in the world coordinates where z=0 (just for this case),
            # I have to find the right value of z to use while creating a 4D point from the 2D mouse position. This will ensure
            # that the world position
            p = world2screen_transformation * glm.vec4(random(), random(), 0.0, 1.0)
            p /= p.w
            z_value = p.z
            # Multiply normalized_mouse_pos with it
            mouse_pos_in_world = screen2world_transformation * glm.vec4(normalized_mouse_pos, z_value, 1.0)
            mouse_pos_in_world /= mouse_pos_in_world.w

            # dest = glm.vec3(opponent.position.x, opponent.position.y, opponent.position.z - 5.0)
            pos_xy = mouse_pos_in_world.xy
            dest = glm.vec3(pos_xy, -13.0)
            if SuperShot == False:
                player.shoot(destination=dest)
            else:
                player.shoot(glm.vec3(opponent.position.x, opponent.position.y, opponent.position.z - 1))

        # else:
        #     target = glm.vec3(x / screen_size.x, y / screen_size.y, 0.0)
        #     camera.setTarget(target)

    if button == 2 and state == 0:
        print(Active_Bullets_Referee)

        for bullet in Active_Bullets_Referee:
            print(bullet.destination)
            print(bullet.position)


glut.glutMouseFunc(mouse_button_input)

def mouse_motion(x, y):  # x any y is the mouse positions
    global FreeCamera
    if FreeCamera:
        target = glm.vec3(x / screen_size.x, y / screen_size.y, 0.0)
        camera.setTarget(target)


glut.glutMotionFunc(mouse_motion)

# Creating a Shader Program -------------------------------------------------------|
# Compile shaders [shorthand]
vertex_shader = shaders.compileShader("""#version 330
layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec2 vertex_texture_position;
layout(location = 2) in vec3 vertex_normal;
uniform mat4 projection;
uniform mat4 view;
uniform mat4 transformation;

uniform mat4 lightSpaceMatrix;

out vec2 texture_position;
out vec3 normal;
out vec3 world_position;


out vec4 FragPosLightSpace;

void main()
{
    //Because the transformation matrix is 4x4, we have to construct a vec4 from position, so we can multiply them
    vec4 pos = vec4(vertex_position, 1.0);
    gl_Position = projection * view * transformation * pos;

    texture_position = vertex_texture_position;

    vec4 transformed_normal = transpose(inverse(transformation)) * vec4(vertex_normal, 0.0);
    normal = normalize(transformed_normal.xyz);

    world_position = (transformation * pos).xyz;

    FragPosLightSpace = lightSpaceMatrix * vec4(world_position, 1.0);
}
""", gl.GL_VERTEX_SHADER)

fragment_shader = shaders.compileShader("""#version 420
layout(binding = 0) uniform sampler2D ambient_color_sampler;
layout(binding = 1) uniform sampler2D diffuse_color_sampler;
layout(binding = 2) uniform sampler2D shadowMap;

in vec2 texture_position;
in vec3 normal;
in vec3 world_position;
in vec4 FragPosLightSpace;


uniform vec3 light_position;
uniform vec3 camera_position;
uniform vec3 color;

uniform vec3 ambient_color;
uniform vec3 diffuse_color;
uniform vec3 specular_color;
uniform float shininess;

out vec4 fragment_color;

float ShadowCalculation(vec4 fragPosLightSpace)
{
    // perform perspective divide
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    // transform to [0,1] range
    projCoords = projCoords * 0.5 + 0.5;
    // get closest depth value from light's perspective (using [0,1] range fragPosLight as coords)
    float closestDepth = texture(shadowMap, projCoords.xy).r; 
    // get depth of current fragment from light's perspective
    float currentDepth = projCoords.z;
    // check whether current frag pos is in shadow
    float bias = 0.0005;
    float shadow = currentDepth - bias > closestDepth  ? 1.0 : 0.0;

    return shadow;
}

void main()
{
    float shadow = ShadowCalculation(FragPosLightSpace);

    vec3 ambient_color = color;
    float ambient_intensity = 0.5;

    vec3 color = (ambient_color + texture(ambient_color_sampler, texture_position).xyz) * ambient_intensity;

    vec3 diffuse_color = color;
    float diffuse_intensity = 0.9;
    float light_intensity = dot(
        -normalize(vec3(0.0, 0.0, -4.0) - light_position),
        normal
    );

    //color += diffuse_color * diffuse_intensity * max(0.0, light_intensity);
    color += ((diffuse_color + texture(diffuse_color_sampler, texture_position).xyz) * diffuse_intensity * max(0.0, light_intensity)) * (1- shadow);

    if (light_intensity > 0.0)
    {
        float specular_intensity = 1.0;
        vec3 light_reflection = reflect(
            -normalize(light_position - vec3(0.0, 0.0, -4.0)),
            normal
        );
        float reflection_intensity = dot(
            normalize(camera_position - world_position),
            light_reflection
        );

        color += (specular_color * specular_intensity * max(0.0, pow(max(0.0, reflection_intensity), shininess))) * (1- shadow);
    }

    fragment_color = vec4(color, 1.0);
    //fragment_color = vec4(float(shadow), texture(shadowMap, texture_position).r, 0.0, 1.0);
}
""", gl.GL_FRAGMENT_SHADER)

# Compile the program [shorthand]
shader_program = shaders.compileProgram(vertex_shader, fragment_shader)

# Set the program we just created as the one in use
gl.glUseProgram(shader_program)

# Get the transformation location
transformation_location = gl.glGetUniformLocation(shader_program, "transformation")

# Get the view location
view_location = gl.glGetUniformLocation(shader_program, "view")

# Get the projection location
projection_location = gl.glGetUniformLocation(shader_program, "projection")

# Set the light_position uniform
light_position = glm.vec3(-3.0, 6.0, 6)
light_position_location = gl.glGetUniformLocation(shader_program, "light_position")
gl.glUniform3fv(light_position_location, 1, glm.value_ptr(light_position))

# Get the camera_position location
camera_position_location = gl.glGetUniformLocation(shader_program, "camera_position")

lightSpaceMatrix_location_Main = gl.glGetUniformLocation(shader_program, "lightSpaceMatrix")

# Get the material uniforms' locations
ambient_color_location = gl.glGetUniformLocation(shader_program, "ambient_color")
diffuse_color_location = gl.glGetUniformLocation(shader_program, "diffuse_color")
specular_color_location = gl.glGetUniformLocation(shader_program, "specular_color")
shininess_location = gl.glGetUniformLocation(shader_program, "shininess")

# SHADOW
# Creating a FrameBuffer Object named as depthMapFBO
depthMapFBO = gl.glGenFramebuffers(1)

# Creating a 2D texture that we'll use as the framebuffer's depth buffer:
SHADOW_WIDTH = 5120
SHADOW_HEIGHT = 5120

depthMap = gl.glGenTextures(1)
gl.glBindTexture(gl.GL_TEXTURE_2D, depthMap)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT, SHADOW_WIDTH, SHADOW_HEIGHT, 0, gl.GL_DEPTH_COMPONENT,
                gl.GL_FLOAT, None)

# With the generated depth texture we can attach it as the framebuffer's depth buffer
gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, depthMapFBO)
gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_TEXTURE_2D, depthMap, 0)
gl.glDrawBuffer(gl.GL_NONE)
gl.glReadBuffer(gl.GL_NONE)
gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

# # 1. first render to depth map
near_plane = 0.0
far_plane = 70.0
lightProjection = glm.ortho(-10.0, 10.0, -10.0, 10.0, near_plane, far_plane)
lightView = glm.lookAt(light_position, glm.vec3(0.0, 0.0, -4.0),
                       glm.vec3(0.0, 1.0, 0.0))  # light's view, looking at the center of the scene
lightSpaceMatrix = lightProjection * lightView

# Create simpleDepthShader
vertex_shader2 = shaders.compileShader("""#version 330
layout(location = 0) in vec3 position;
uniform mat4 lightSpaceMatrix;
uniform mat4 transformation;

void main()
{
    gl_Position = lightSpaceMatrix * transformation * vec4(position, 1.0);
}
""", gl.GL_VERTEX_SHADER)

fragment_shader2 = shaders.compileShader("""#version 330
void main()
{
    //gl_FragDepth = gl_FragCoord.z;
}
""", gl.GL_FRAGMENT_SHADER)

simpleDepthShader = shaders.compileProgram(vertex_shader2, fragment_shader2)
gl.glUseProgram(simpleDepthShader)
lightSpaceMatrix_location = gl.glGetUniformLocation(simpleDepthShader, "lightSpaceMatrix")
transformation_location2 = gl.glGetUniformLocation(simpleDepthShader, "transformation")

gl.glUniformMatrix4fv(lightSpaceMatrix_location, 1, False, glm.value_ptr(lightSpaceMatrix))

# Creating Data Buffers -----------------------------------------------------------|
# With the ability of .obj file loading, all the data will be read from the files and bound to proper buffers

custom_cylinder_object = parse_and_bind_obj_file("Assets/Primitives/cylinder.obj")
custom_plane_object = parse_and_bind_obj_file("Assets/Primitives/plane.obj")
custom_sphere_object = parse_and_bind_obj_file("Assets/Primitives/sphere.obj")
custom_disc_object = parse_and_bind_obj_file("Assets/Primitives/disc.obj")

custom_haystack_object = parse_and_bind_obj_file("Assets/Primitives/sphere.obj")
texture = load_image_to_texture("haystack.jpg")
custom_haystack_object.meshes[0].material.map_Ka = texture
custom_haystack_object.meshes[0].material.map_Kd = texture

custom_crate_object = parse_and_bind_obj_file("Assets/Primitives/cube.obj")
texture2 = load_image_to_texture("crate.png")
custom_crate_object.meshes[0].material.map_Ka = texture2
custom_crate_object.meshes[0].material.map_Kd = texture2

custom_gameLost_object = parse_and_bind_obj_file("Assets/Primitives/plane.obj")
texture3 = load_image_to_texture("gameover.jpg")
custom_gameLost_object.meshes[0].material.map_Ka = texture3
custom_gameLost_object.meshes[0].material.map_Kd = texture3

custom_gameWon_object = parse_and_bind_obj_file("Assets/Primitives/plane.obj")
texture4 = load_image_to_texture("gamewon.jpg")
custom_gameWon_object.meshes[0].material.map_Ka = texture4
custom_gameWon_object.meshes[0].material.map_Kd = texture4
# Configure GL -----------------------------------------------------------------------|

# Enable depth test
gl.glEnable(gl.GL_DEPTH_TEST)
# Accept fragment if it closer to the camera than the former one
gl.glDepthFunc(gl.GL_LESS)

# Create Camera and Game Objects -----------------------------------------------------|

perspective_projection = glm.perspective(glm.radians(45.0), screen_size.x / screen_size.y, 0.1, 100.0)

player = Player(custom_cylinder_object, position=glm.vec3(0.0, 0.0, -3.0), scale=glm.vec3(0.20))
camera = Camera(player, position=glm.vec3(0.0, 3.0, 12.0), target=player.position)
opponent = Opponent(custom_cylinder_object, position=glm.vec3(0.0, 0.0, -4.0), scale=glm.vec3(0.20))
spectator1 = Spectator(custom_cylinder_object, position=glm.vec3(2.0, 0.0, -4.0), scale=glm.vec3(0.20))
spectator2 = Spectator(custom_cylinder_object, position=glm.vec3(-2.0, 0.0, -4.0), scale=glm.vec3(0.20))
ground = Ground(custom_plane_object, position=glm.vec3(0.0, -0.20, -4.0), scale=glm.vec3(10))
haystack = Haystack(custom_haystack_object, position=glm.vec3(-5.0, 0.0, 5.0), scale=glm.vec3(0.15))
crate1 = Crate(custom_crate_object, position=glm.vec3(2.0, -0.05, -3.0), scale=glm.vec3(0.15))
crate2 = Crate(custom_crate_object, position=glm.vec3(-2.0, -0.05, -3.0), scale=glm.vec3(0.15))
gamelost = GameOver(custom_gameLost_object, position=glm.vec3(0.0, 0.0, 0.0), scale=glm.vec3(8.0))
gamewon = GameOver(custom_gameWon_object, position=glm.vec3(0.0, 0.0, 0.0), scale=glm.vec3(4.0, 8.0, 8.0))

collision_testers = []
collision_testers.append(opponent)
collision_testers.append(player)

# Start the main loop
glut.glutMainLoop()
