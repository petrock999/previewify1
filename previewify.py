import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox
from PyQt5.QtCore import Qt, QUrl, QCoreApplication
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PyQt5.QtGui import QFont, QIcon

from PyQt5.QtWidgets import QInputDialog, QListWidgetItem
from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtGui import QClipboard

# Add your own credentials
SPOTIPY_CLIENT_ID = 'ADD YOUR OWN CLIENT ID'
SPOTIPY_CLIENT_SECRET = 'ADD YOUR OWN CLIENT SECRET'
SPOTIPY_REDIRECT_URI = 'http://localhost:8000/callback'

scope = "playlist-read-private"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=scope))

class SpotifyPlaylistApp(QWidget):
    def __init__(self):
        super().__init__()
        self.preview_urls = [] 
        self.initUI()

        
    def initUI(self):
        self.setWindowTitle('Spotify Playlist Preview')

        # Window Size and Font
        self.setFixedSize(400, 500)
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.url_label = QLabel('Enter Spotify Playlist URL:', self)
        layout.addWidget(self.url_label)
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Paste Spotify Playlist URL here...")
        layout.addWidget(self.url_input)

        self.search_album_label = QLabel('Or search for an album:', self)
        layout.addWidget(self.search_album_label)
        self.search_album_input = QLineEdit(self)
        self.search_album_input.setPlaceholderText("Type album name here...")
        layout.addWidget(self.search_album_input)

        # Album Search Button
        self.search_album_button = QPushButton('Search Album', self)
        self.search_album_button.clicked.connect(self.search_album)
        layout.addWidget(self.search_album_button)

        # Load Button
        self.load_button = QPushButton('Load Playlist', self)
        self.load_button.clicked.connect(self.load_playlist)
        self.load_button.setFixedHeight(40)  
        layout.addWidget(self.load_button)

        # Track List
        self.track_list = QListWidget(self)
        layout.addWidget(self.track_list)

        # Player controls layout
        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)

        # Previous, Play and Next buttons
        self.previous_button = QPushButton('Previous', self)
        self.previous_button.setEnabled(False)
        self.previous_button.clicked.connect(self.play_previous)
        control_layout.addWidget(self.previous_button)

        self.play_button = QPushButton('Play', self)
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.play_pause)
        control_layout.addWidget(self.play_button)

        self.next_button = QPushButton('Next', self)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.play_next)
        control_layout.addWidget(self.next_button)

        layout.addLayout(control_layout)

        # Connect track list selection change to update controls
        self.track_list.itemSelectionChanged.connect(self.update_controls)

        # Main Media Player
        self.media_player = QMediaPlayer(self)
        self.media_player.mediaStatusChanged.connect(self.media_status_changed)

        self.setStyleSheet("""
            QWidget {
                background-color: #2C2C2C;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #1DB954;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 5px 20px;
            }
            QPushButton:hover {
                background-color: #189E40;
            }
            QPushButton:disabled {
                background-color: #4A4A4A;
                color: #B3B3B3;
            }
            QLineEdit {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 5px 10px;
            }
            QListWidget {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #1DB954;
            }

            /* QScrollBar styling starts here */
            QScrollBar:vertical {
                background: #4A4A4A;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #1DB954;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar:horizontal {
                background: #4A4A4A;
                height: 10px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #1DB954;
                min-width: 20px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }
        """)


    def search_album(self):
        album_query = self.search_album_input.text()
        if album_query:
            try:
                results = sp.search(q='album:' + album_query, type='album')
                albums = results['albums']['items']
                if albums:
                    album_names = [f"{album['name']} - {album['artists'][0]['name']}" for album in albums]
                    item, ok = QInputDialog.getItem(self, "Select an Album", "Albums:", album_names, 0, False)
                    if ok and item:
                        selected_album = albums[album_names.index(item)]
                        album_url = selected_album['external_urls']['spotify']
                        self.url_input.setText(album_url)
                else:
                    QMessageBox.warning(self, "No Results", "No albums found matching your query.")
            except spotipy.exceptions.SpotifyException as e:
                QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")


    def load_playlist(self):
        spotify_url = self.url_input.text()

        self.playlist_id = None
        self.album_id = None
        self.track_list.clear()
        self.preview_urls.clear() 

        if "spotify:playlist:" in spotify_url:
            self.playlist_id = spotify_url.split("spotify:playlist:")[1].split('?')[0]
        elif "open.spotify.com/playlist/" in spotify_url:
            self.playlist_id = spotify_url.split("open.spotify.com/playlist/")[1].split('?')[0]
        elif "spotify:album:" in spotify_url:
            self.album_id = spotify_url.split("spotify:album:")[1].split('?')[0]
        elif "open.spotify.com/album/" in spotify_url:
            self.album_id = spotify_url.split("open.spotify.com/album/")[1].split('?')[0]

        # Fetch and display data
        try:
            if self.playlist_id:
                results = sp.playlist_tracks(self.playlist_id)
                items = results['items']
                for item in items:
                    track = item['track']
                    self.track_list.addItem(f"{track['name']} - {track['artists'][0]['name']}")
                    self.preview_urls.append(track['preview_url'])
            elif self.album_id:
                results = sp.album_tracks(self.album_id)
                items = results['items']
                for track in items:
                    self.track_list.addItem(f"{track['name']} - {track['artists'][0]['name']}")
                    self.preview_urls.append(track['preview_url'])

            if self.preview_urls:
                self.media_player.setMedia(QMediaContent(QUrl(self.preview_urls[0])))

        except spotipy.exceptions.SpotifyException as e:
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")
            return


    def play_pause(self):
        selected_preview_url = self.get_current_track_preview_url()
        if not selected_preview_url:
            return

        current_media = self.media_player.currentMedia().canonicalResource().url().toString()


        if selected_preview_url != current_media:
            self.media_player.setMedia(QMediaContent(QUrl(selected_preview_url)))
            self.media_player.play()
        else:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()

    def play_previous(self):
        current_row = self.track_list.currentRow()
        if current_row > 0:
            self.track_list.setCurrentRow(current_row - 1)
            self.media_player.setMedia(QMediaContent(QUrl(self.get_current_track_preview_url())))
            self.media_player.play()

    def play_next(self):
        current_row = self.track_list.currentRow()
        if current_row < self.track_list.count() - 1:
            self.track_list.setCurrentRow(current_row + 1)
            self.media_player.setMedia(QMediaContent(QUrl(self.get_current_track_preview_url())))
            self.media_player.play()

    def get_current_track_preview_url(self):
        selected_items = self.track_list.selectedItems()
        if selected_items:
            index = self.track_list.row(selected_items[0])
            return self.preview_urls[index]
        return None

    def update_controls(self):
        selected_items = self.track_list.selectedItems()
        if selected_items:
            self.play_button.setEnabled(True)
            index = self.track_list.row(selected_items[0])

            if self.playlist_id:
                results = sp.playlist_tracks(self.playlist_id)
            elif self.album_id:
                results = sp.album_tracks(self.album_id)
            else:
                return  
                

            tracks = results['items']

            tracks = results['items']
            if tracks:
                if index > 0:
                    self.previous_button.setEnabled(True)
                else:
                    self.previous_button.setEnabled(False)
                if index < len(tracks) - 1:
                    self.next_button.setEnabled(True)
                else:
                    self.next_button.setEnabled(False)
        else:
            self.play_button.setEnabled(False)
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)

    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            current_row = self.track_list.currentRow()
            if current_row < self.track_list.count() - 1:
                self.track_list.setCurrentRow(current_row + 1)
                self.media_player.setMedia(QMediaContent(QUrl(self.get_current_track_preview_url())))
                self.media_player.play()

def main():
    app = QApplication(sys.argv)
    window = SpotifyPlaylistApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
