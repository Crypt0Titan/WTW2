import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import io from 'socket.io-client';
import { API_URL, SOCKET_URL } from '../config';

const socket = io(SOCKET_URL);

export default function GameLobbyScreen({ route, navigation }) {
  const { gameId } = route.params;
  const [game, setGame] = useState(null);
  const [players, setPlayers] = useState([]);
  const [countdown, setCountdown] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGameDetails();

    socket.emit('join', { game_id: gameId });

    socket.on('player_joined', (data) => {
      if (data.game_id === gameId) {
        setPlayers(prevPlayers => [...prevPlayers, data.player]);
      }
    });

    socket.on('game_started', (data) => {
      if (data.game_id === gameId) {
        navigation.navigate('PlayGame', { gameId });
      }
    });

    const timer = setInterval(updateCountdown, 1000);

    return () => {
      socket.off('player_joined');
      socket.off('game_started');
      clearInterval(timer);
    };
  }, [gameId]);

  const fetchGameDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/games/${gameId}`);
      const data = await response.json();
      setGame(data);
      setPlayers(data.players);
    } catch (error) {
      console.error('Error fetching game details:', error);
      Alert.alert('Error', 'Unable to fetch game details. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const updateCountdown = () => {
    if (game && game.start_time) {
      const now = new Date();
      const startTime = new Date(game.start_time);
      const timeLeft = startTime - now;
      if (timeLeft > 0) {
        const minutes = Math.floor(timeLeft / 60000);
        const seconds = Math.floor((timeLeft % 60000) / 1000);
        setCountdown(`${minutes}:${seconds < 10 ? '0' : ''}${seconds}`);
      } else {
        setCountdown('Game starting...');
      }
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#0000ff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Game Lobby</Text>
      <Text style={styles.countdown}>Time until start: {countdown}</Text>
      <Text style={styles.subtitle}>Players in Lobby</Text>
      <FlatList
        data={players}
        renderItem={({ item }) => <Text style={styles.playerItem}>{item.ethereum_address}</Text>}
        keyExtractor={item => item.id.toString()}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  countdown: {
    fontSize: 18,
    marginBottom: 20,
  },
  subtitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  playerItem: {
    fontSize: 16,
    marginBottom: 5,
  },
});
