import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface OpenWeatherData {
    main: {
        temp: number;
        humidity: number;
        feels_like: number;
    };
    weather: {
        main: string;
        description: string;
    }[];
    wind: {
        speed: number;
    };
    visibility: number;
    name: string;
    sys: {
        country: string;
    };
}

interface OpenMeteoData {
    current: {
        weather_code: number;
    };
    daily: {
        time: string[];
        uv_index_max: number[];
        temperature_2m_max: number[];
        temperature_2m_min: number[];
        weather_code: number[];
        precipitation_probability_max: number[];
        rain_sum: number[];
    };
    hourly: {
        time: string[];
        temperature_2m: number[];
    };
}

interface WeatherContextType {
    weatherData: OpenWeatherData | null;
    forecastData: OpenMeteoData | null;
    locationName: string;
    loading: boolean;
    error: string | null;
    fetchWeatherByCity: (city: string) => void;
    useCurrentLocation: () => void;
}

const WeatherContext = createContext<WeatherContextType | undefined>(undefined);

const OPENWEATHER_API_KEY = '5b88263f64d6c71a355d39ea646359c6';

export const WeatherProvider = ({ children }: { children: ReactNode }) => {
    const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);
    const [locationName, setLocationName] = useState<string>('Loading...');
    const [weatherData, setWeatherData] = useState<OpenWeatherData | null>(null);
    const [forecastData, setForecastData] = useState<OpenMeteoData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchWeatherByCoords = async (lat: number, lon: number) => {
        setLoading(true);
        setError(null);
        try {
            const [weatherRes, forecastRes] = await Promise.all([
                fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${OPENWEATHER_API_KEY}&units=metric`),
                fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=weather_code,sunrise,sunset,uv_index_max,rain_sum,temperature_2m_max,temperature_2m_min,apparent_temperature_max,snowfall_sum,precipitation_sum,precipitation_hours,precipitation_probability_max&hourly=temperature_2m,relative_humidity_2m,rain,snowfall,weather_code,wind_speed_10m&current=temperature_2m,relative_humidity_2m,is_day,rain,snowfall,weather_code,wind_speed_10m,wind_direction_10m,cloud_cover,precipitation&timezone=auto&past_days=1`)
            ]);

            if (!weatherRes.ok || !forecastRes.ok) {
                throw new Error('Failed to fetch weather data from one or more sources.');
            }

            const current = await weatherRes.json();
            const forecast = await forecastRes.json();
            
            setLocationName(`${current.name}, ${current.sys.country}`);
            setWeatherData(current);
            setForecastData(forecast);

        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch weather data.';
            setError(errorMessage);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchWeatherByCity = async (city: string) => {
        setLoading(true);
        setError(null);
        try {
            const geoRes = await fetch(`https://api.openweathermap.org/geo/1.0/direct?q=${city}&limit=1&appid=${OPENWEATHER_API_KEY}`);
            const geoData = await geoRes.json();
            if (geoData && geoData.length > 0) {
                const { lat, lon } = geoData[0];
                setLocation({ lat, lon });
                // The useEffect will trigger fetchWeatherByCoords
            } else {
                setError(`Could not find location: ${city}`);
                setLoading(false);
            }
        } catch (err) {
            setError('Failed to fetch location data.');
            console.error(err);
            setLoading(false);
        }
    };

    const useCurrentLocation = () => {
        setLoading(true);
        setError(null);
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    setLocation({ lat: latitude, lon: longitude });
                },
                () => {
                    setError('Geolocation permission denied. Please enter a location manually or grant permission.');
                    setLoading(false);
                    // Fallback to a default location if permission is denied
                    fetchWeatherByCity('Delhi');
                }
            );
        } else {
            setError('Geolocation is not supported by this browser.');
            setLoading(false);
            // Fallback to a default location
            fetchWeatherByCity('Delhi');
        }
    };

    useEffect(() => {
        if (location) {
            fetchWeatherByCoords(location.lat, location.lon);
        } else {
            // Call useCurrentLocation directly, not inside useEffect
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const { latitude, longitude } = position.coords;
                        fetchWeatherByCoords(latitude, longitude);
                    },
                    (error) => {
                        console.error('Error getting location:', error);
                        setError('Unable to get your location. Using default location.');
                        setLoading(false);
                        fetchWeatherByCity('Delhi');
                    }
                );
            } else {
                setError('Geolocation is not supported by this browser.');
                setLoading(false);
                fetchWeatherByCity('Delhi');
            }
        }
    }, [location]);

    const value = { weatherData, forecastData, locationName, loading, error, fetchWeatherByCity, useCurrentLocation };

    return <WeatherContext.Provider value={value}>{children}</WeatherContext.Provider>;
};

export const useWeather = () => {
    const context = useContext(WeatherContext);
    if (context === undefined) {
        throw new Error('useWeather must be used within a WeatherProvider');
    }
    return context;
};