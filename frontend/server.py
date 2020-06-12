from flask import Flask
from flask import request, Response, render_template, json, url_for
from flask_restful import reqparse, abort, Api, Resource
import os
import base64
from io import BytesIO
import qrcode
import time
import threading

# Create an instance of Flask API
app = Flask(__name__) 
api = Api(app)

# TODO: did it get used?
parser = reqparse.RequestParser()
parser.add_argument('task') 

# Create a URL route in our application for "/"
@app.route('/')
def home():
    """
    This function just responds to the browser ULR
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template('index.html')

# For developing purpose - test camera toggle
@app.route('/test_tab')
def test_tab():
    return render_template('test_tab.html')


class ImageHandler(Resource):

    def post(self):
        # image_data = request.form.get('upimage')
        image_data = request.files.get('upimage')
        print(image_data)
        if image_data is not None:
            image_data.save('image.jpg')
        else:
            print('Warning: Empty picture! Make sure that the browser has the permission to use the camera.')
        # with open('image.png', 'wb') as fout:
            # fout.write(image_data)

class QRGenerator(Resource):

    def post(self):
        print('The param is', request.form.get('text_data'))
        print(app.instance_path)
        img_qr = qrcode.make(request.form.get('text_data'))
        # return json.dumps({'src': os.path.join(app.root_path, 'qr.png')})
        # return json.dumps({'src': '../qr.png'})
        # print(img_qr)
        # buffered = BytesIO()
        img_qr.save('qr.png')
        # return json.dumps({'src': base64.b64encode(buffered.getvalue)})
        return json.dumps({'src': url_for('static', filename='qr.png')})


class RelayServer(Resource):

    def __init__(self):
        super(RelayServer, self).__init__()
        
        # Directory for rendered images
        self.output_dir = 'output'

        # For support multiple users
        self.user_id = 0
        self.active_users = []

        # TODO: what does movie_link_dict mean?
        self.movie_link_dict = dict()
        self.last_sharable_movie_link = None 


    def movie_upload_daemon(self):
        """
        Create a daemon thread, so that it keeps checking whether a new movie is generated,
        and if so, upload to the shared drive.
        """

        # TODO: login to SURFdrive, upload movie, get sharable link
        # def upload_movie_to_drive(active_user, output_dir):
        #     movie_path = os.path.join(output_dir, str(active_user), 'video.mp4')

        #     new_video_fn = 'video_%s.mp4' % output_dir
        #     shared_link = None
        #     return shared_link

        def check_upload(active_users_list, output_dir, movie_link_dict):
            while True:
                print('Checking %d active users' % len(active_users_list))
                link_dict = dict()
                for active_user in active_users_list:
                    # check if movie exists
                    movie_path = os.path.join(output_dir, str(active_user), 'video.mp4')
                    if os.path.isfile(movie_path):
                        # movie exists. Check whether it is uploaded to the server.
                        if movie_path in movie_link_dict.values():
                            # movie has been shared. Remove from monitoring
                            active_users_list.remove(active_user)
                        else:
                            # check whether movie is fully sync'ed by determining whether an empty file `DONE` is present
                            if os.path.isfile(os.path.join(output_dir, str(active_user), 'DONE')):
                                # movie is fully downloaded, upload the movie now
                                # shared_link = upload_movie_to_drive(active_user, output_dir)
                                # link_dict[movie_path] = shared_link
                                print('movie_path', movie_path, url_for('static', filename=movie_path))
                                movie_link_dict[active_user] = movie_path
                            else:
                                # movie is still downloading. Just wait
                                pass
                time.sleep(5)
        try:
            th = threading.Thread(target=check_upload, args=(self.active_users, self.output_dir, self.movie_link_dict))
            th.start()
            return th
        except:
            print('Error: unable to start the daemon!')
            return None

    def get(self):
        """
        Using HTTP GET to submit an ID (which is the timestamp) of the rendered movie.

        Return: The URL of the movie if it is ready. Otherwise return an empty URL.
        """
        ts = request.args.get('movie_id')
        print('Get a request')
        movie_path = os.path.join(self.output_dir, str(ts), 'video.mp4')

        if os.path.isfile(movie_path):
            movie_shared_url = 'https://home.maxwellcai.com/learning_to_paint_videos/video_output/%s.mp4' % str(ts)
            print('sharable', movie_shared_url)
            return json.dumps({'src': url_for('static', filename=movie_path), 'sharable': movie_shared_url})
        else:
            return json.dumps({'src': ""})  # return empty URL if movie is not yet ready

    def post(self):
        image_data = request.files.get('upimage')
    
        if image_data is not None:
            timestamp = time.time()
            self.active_users.append(timestamp)
            user_output_dir = os.path.join(self.output_dir, str(timestamp))
            print("user_output_dir", user_output_dir)
            if not os.path.isdir(user_output_dir):
                os.makedirs(user_output_dir)

            # save camera image.
            print("Save camera images...")
            image_data.save(os.path.join(user_output_dir, 'image.jpg'))

            # generate the movie frame
            orig_dir = os.getcwd()
            os.chdir(user_output_dir)
            print('Generating frames...')
            os.system('python /Users/pennyqxr/Code/LearningToPaintDemo/baseline/test.py --img image.jpg --actor /Users/pennyqxr/Code/LearningToPaintDemo/baseline/model/actor.pkl --renderer /Users/pennyqxr/Code/LearningToPaintDemo/baseline/model/renderer.pkl')

            # generate the movie
            print('Generate movie...')
            os.system('ffmpeg -r 30 -f image2 -i output/generated_%05d.jpg -s 512x512 -c:v libx264 -pix_fmt yuv420p video.mp4 -q:v 0 -q:a 0')
            os.system('touch DONE')

            # upload the movie to a HTTPS server
            os.system('scp -i /Users/pennyqxr/.ssh/id_rsa_pi -P 13893 video.mp4 pi@home.maxwellcai.com:/var/www/html/learning_to_paint_videos/video_%s.mp4' % user_output_dir)

            # get back to the original dir
            os.chdir(orig_dir)

            # generate QR code of the movie
            movie_shared_url = 'https://home.maxwellcai.com/learning_to_paint_videos/video_output/%s.mp4' % str(timestamp)
            self.last_sharable_movie_link = movie_shared_url
            qr_link = self.generate_qr_code(movie_shared_url, timestamp)
            self.user_id += 1
            return json.dumps({'src': qr_link, 'ts': timestamp, 'sharable': movie_shared_url})
        else:
            print('Warning: Empty picture! Make sure that the browser has the permission to use the camera.')

    def generate_qr_code(self, shared_link, timestamp):
        """
        Generate a QR code so that the user can download the rendered movie.

        Return: a JSON string with the URL of the QR code (to be displayed in the web interface).
        """
        img_qr = qrcode.make(shared_link)
        try:
            if not os.path.isdir('static/qr'):
                os.makedirs('static/qr')
            img_qr.save(os.path.join('static/qr', 'qr_%s.png' % str(timestamp)))
        except OSError as error:
            print("Error when generate QR code", error)
            return None
        # return json.dumps({'src': url_for('static', filename='qr.png')})
        return url_for('static', filename='qr/qr_%s.png' % str(timestamp))


##
## Actually setup the Api resource routing here
##
api.add_resource(ImageHandler, '/upload')
api.add_resource(QRGenerator, '/qr')
api.add_resource(RelayServer, '/server')

# Start the application by running as the main program itself
if __name__ == '__main__':
    app.run(debug=True)
