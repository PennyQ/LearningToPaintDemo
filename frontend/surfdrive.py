import owncloud

oc = owncloud.Client('https://surfdrive.surf.nl/files')

oc.login('veldd@surfsara.nl', 'RXBCHmDV6DIX')

oc.mkdir('testdir')

oc.put_file('testdir/image.png', 'image.png')

link_info = oc.share_file_with_link('testdir/remotefile.txt')

print("Here is your link: " + link_info.get_link())