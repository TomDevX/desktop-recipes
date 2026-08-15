import QtQuick
import QtMultimedia

Item {
    id: root
    width: Screen.width
    height: Screen.height

    Rectangle {
        anchors.fill: parent
        color: "black"
    }

    MediaPlayer {
        id: player
        source: Qt.resolvedUrl("video.mp4")
        videoOutput: videoOutput
        audioOutput: AudioOutput {}
        loops: MediaPlayer.Infinite
        Component.onCompleted: player.play()
    }

    VideoOutput {
        id: videoOutput
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectCrop
    }

    Text {
        id: date
        text: Qt.formatDateTime(new Date(), "dddd dd ' | ' MMMM yyyy")
        font.pointSize: 32
        color: "#ffffff"
        opacity: 1.0
        font {
            family: "Noto Sans"
            weight: Font.Bold
            capitalization: Font.MixedCase
        }
        style: Text.Outline
        styleColor: "#80000000"
        anchors.horizontalCenter: parent.horizontalCenter
        y: (parent.height - height) / 1.1
    }
}
