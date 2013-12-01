#coding: utf-8
#footprint database server

import os
import hashlib
import pymongo
import tornado.web
import tornado.httpserver
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("footprint_database", default="footprintDB", help="footprint database name")
define("users_collection", default="usersColl", help="footprint users' name and pwd")
define("lines_collection", default="linesColl", help="footprint lines' name, creator, create time, update time ...")

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/", HomeHandler),
			(r"/register", RegisterHandler),
			(r"/login", LoginHandler),
			(r"/logout", LogoutHandler),
			
			(r"/userreg", UserRegHandler),
			(r"/userlogin", UserLoginHandler),
			(r"/datahandle", DataHandler),
			
		]
		settings = dict(
			title="footprint",
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
			cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
			debug=True,
		)
		tornado.web.Application.__init__(self, handlers, **settings)
		
		self.db = pymongo.Connection()[options.footprint_database]

class BaseHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db

	def get_current_user(self):
		username = self.get_secure_cookie("username")
		if not username: return None
		username = username.decode(encoding='UTF-8',errors='strict') #python3.3.3编码要求
		return self.db[options.users_collection].find_one({"username": (username),})

	def Login(self, username, pwd):
		if not username or not pwd:
			self.write("用户名和密码均不能为空")
			return
		pwd = pwd.encode('utf-8') #为兼容python3.3.3版本的haslib模块
		pwd = hashlib.new("md5", pwd).hexdigest()
		coll = self.db[options.users_collection]
		user = coll.find_one({"username": username, "pwd":pwd})
		if user:
			self.write("登陆成功！")
			self.set_secure_cookie("username", username)
		else:
			self.write("账号密码不匹配哦~~再试一下")
			
	def Register(self, username, pwd):
		coll = self.db[options.users_collection]
		if coll.find_one({"username": username}):
			self.write("该用户名已经被注册，重新选择一个吧")
			return
		
		pwd = pwd.encode('utf-8') #为兼容python3.3.3版本的haslib模块
		pwd = hashlib.new("md5", pwd).hexdigest()
		coll.insert({"username":username, "pwd":pwd})
		self.write("恭喜注册成功！")

class HomeHandler(BaseHandler):
	def get(self):
		self.render("home.html")
		
class RegisterHandler(BaseHandler):
	def get(self):
		self.render("register.html")

class UserRegHandler(BaseHandler):
	def post(self):
		username = self.get_argument("username", "")
		pwd = self.get_argument("password", "")
		pwd2 = self.get_argument("password2", "")
		if not username or not pwd or not pwd2:
			self.write("用户名和密码均不能为空")
			return
		
		if pwd != pwd2:
			self.write("两个密码不一样哦~")
			return
		
		self.Register(username, pwd)

class LoginHandler(BaseHandler):
	def get(self):
		self.render("login.html")

class UserLoginHandler(BaseHandler):
	def post(self):
		username = self.get_argument("username", "")
		pwd = self.get_argument("password", "")
		self.Login(username, pwd)

C2DS_USERREGISTER = 1
C2DS_USERLOGIN = 2

class DataHandler(BaseHandler):
	def get(self):
		if not self.get_current_user():
			self.write("您尚未登录")
			return
		
		self.render("datahandle.html")
	
	def post(self):
		data = self.get_argument("data", "None")
		if data == "None":
			self.write("you do not post any thing")
			return 
	
		data = eval(data)
		if not isinstance(data, list):
			self.write("输入数据应该像这样:[1, username, pwd] -- 数据类型应该为列表")
			return
		iKey = data[0]
		if iKey == C2DS_USERREGISTER:
			if len(data) != 3:
				self.write("输入数据应该像这样:[1, username, pwd] -- 注册数据长度不合法")
			username = data[1]
			pwd = data[2]
			self.Register(username, pwd)
		elif iKey == C2DS_USERLOGIN:
			if len(data) != 3:
				self.write("输入数据应该像这样:[1, username, pwd] -- 登录数据长度不合法")
			username = data[1]
			pwd = data[2]
			self.Login(username, pwd)
		
		else:
			self.write("操作类型:%d。数据服务器尚未支持" % iKey)
			
class LogoutHandler(BaseHandler):
	def get(self):
		self.clear_cookie("username")
		self.redirect(self.get_argument("next", "/"))
		
def main():
	print("footprint database srv started ...")
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
	
