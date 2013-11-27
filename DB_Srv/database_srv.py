#coding: utf-8
#footprint database server

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
			
			(r"/userreg", UserRegHandler),
			(r"/userlogin", UserLoginHandler),
			
		]
		settings = dict(
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
		return self.db[options.mongodb_authors].find_one({"username": username})

class HomeHandler(BaseHandler):
	def get(self):
		html = """<html><body>
				<li><a href="/login">login</a></li>
				<li><a href="/register">register</a></li>
				</body><html>
				"""
		self.write(html)
		
class RegisterHandler(BaseHandler):
	def get(self):
		html = """<html>
					<body>
						<form action="/userreg" method="post">
						用户：<input type="text" name="username">
						<br/>
						密码：<input type="password" name="password">
						<input type="submit" value="Submit" />
						</form>
						<p>
							就这么简单，注册吧。
						</p>
					</body>
				</html>
			"""
		self.write(html)

class UserRegHandler(BaseHandler):
	def post(self):
		username = self.get_argument("username", "")
		pwd = self.get_argument("password", "")
		if not username or not pwd:
			self.write("用户名和密码均不能为空")
			return
		coll = self.db[options.users_collection]
		if coll.find_one({"username": username}):
			self.write("该用户名已经被注册，重新选择一个吧")
			return
		coll.insert({"username":username, "pwd":pwd})
		self.write("恭喜注册成功！")

class LoginHandler(BaseHandler):
	def get(self):
		html = """<html>
					<body>
						<form action="/userlogin" method="post">
						用户：<input type="text" name="username">
						<br/>
						密码：<input type="password" name="password">
						<input type="submit" value="Submit" />
						</form>
					</body>
				</html>
			"""
		self.write(html)

class UserLoginHandler(BaseHandler):
	def post(self):
		username = self.get_argument("username", "")
		pwd = self.get_argument("password", "")
		if not username or not pwd:
			self.write("用户名和密码均不能为空")
			return
		coll = self.db[options.users_collection]
		user = coll.find_one({"username": username, "pwd":pwd})
		if user:
			self.write("登陆成功！")
		else:
			self.write("账号密码不匹配哦~~再试一下")
		
def main():
	print("footprint database srv started ...")
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
	
