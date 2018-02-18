from base import BaseHandler, User, database
from tornado.web import authenticated
from os import path
from PIL import Image
import tempfile
import imghdr


class UserHandler(BaseHandler):

    @authenticated
    def get(self, username):
        user = User(username)
        if user.uid is None:
            self.write_error(404, "User not found")
        else:
            self.render("template/user.html", user=self.user, find_user=user)

    @authenticated
    def post(self, username):
        if str(self.get_argument("type_name")) == "avatar_upload":
            if self.request.files.get("avatar", None) is not None:
                avatar = self.request.files.get("avatar")[0]
                if avatar.get("content_type") != "image/jpeg" and avatar.get("content_type") != "image/png":
                    self.render("template/warn.html", title="Error", user=self.user,
                                information='<p>Only accept png or jpeg</p><br/>'
                                            'Click <a href="%s">here</a> to go back' % self.request.path)
                elif len(avatar.get("body")) > 1024 * 1024 / 2:
                    self.render("template/warn.html", title="Error", user=self.user,
                                information='<p>Image size cannot be over 512KB</p><br/>'
                                            'Click <a href="%s">here</a> to go back' % self.request.path)
                else:
                    temp_avatar_file = tempfile.NamedTemporaryFile(delete=True)
                    temp_avatar_file.write(avatar.get("body"))
                    temp_avatar_file.seek(0)
                    if imghdr.what(temp_avatar_file.name) != "jpeg" and imghdr.what(temp_avatar_file.name) != "png":
                        self.render("template/warn.html", title="Error", user=self.user,
                                    information='<p>Only accept png or jpeg</p><br/>'
                                                'Click <a href="%s">here</a> to go back' % self.request.path)
                        temp_avatar_file.close()
                    else:
                        temp_avatar_file.seek(0)
                        avatar_image = Image.open(temp_avatar_file.name)
                        avatar_image.save(path.join(path.realpath(path.dirname(__file__)), "static/img/avatar/%s.png"
                                                    % self.user.username))
                        temp_avatar_file.close()
                        self.render("template/warn.html", title="Success", user=self.user,
                                    information='<p>You have successfully uploaded your avatar<br/>'
                                                'Please force refresh to clear the clear</p><br/>'
                                                'Click <a href="%s">here</a> to go back' % self.request.path)
        elif str(self.get_argument("type_name")) == "user_admin":
            if self.user.permission.get("admin") == 1:
                find_user = User(username)
                permission = find_user.permission
                if self.user.permission.get("gag") == 1:
                    permission.update(dict(connect=int(self.get_argument("connect", default=0))))
                    permission.update(dict(speak=int(self.get_argument("speak", default=0))))
                if self.user.permission.get("root") == 1:
                    permission.update(dict(gag=int(self.get_argument("gag", default=0))))
                    permission.update(dict(admin=int(self.get_argument("admin", default=0))))
                    permission.update(dict(root=int(self.get_argument("root", default=0))))
                database.update("ws_permission", values=permission, where="uid = '%s'" % find_user.uid)
                self.render("template/warn.html", title="Success", user=self.user,
                            information='<p>You have successfully uploaded this user\'s permission<br/>'
                                        'Click <a href="%s">here</a> to go back' % self.request.path)
            else:
                self.render("template/warn.html", title="Error", user=self.user,
                            information='<p>Permission denied<br/>'
                                        'Click <a href="%s">here</a> to go back' % self.request.path)
