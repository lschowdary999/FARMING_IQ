import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { 
  Loader2,
  CloudRain, 
  Sun, 
  Cloud, 
  Thermometer,
  Droplets,
  Wind,
  Eye,
  AlertTriangle,
  Bell,
  MapPin,
  Search,
  Zap
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useWeather } from "@/components/dashboard/WeatherContext";

const WMO_CODES: { [key: number]: { description: string; icon: React.ElementType, emoji: string } } = {
  0: { description: 'Clear sky', icon: Sun, emoji: '☀️' },
  1: { description: 'Mainly clear', icon: Sun, emoji: '☀️' },
  2: { description: 'Partly cloudy', icon: Cloud, emoji: '⛅' },
  3: { description: 'Overcast', icon: Cloud, emoji: '☁️' },
  45: { description: 'Fog', icon: Cloud, emoji: '🌫️' },
  48: { description: 'Depositing rime fog', icon: Cloud, emoji: '🌫️' },
  51: { description: 'Light Drizzle', icon: CloudRain, emoji: '🌦️' },
  53: { description: 'Moderate Drizzle', icon: CloudRain, emoji: '🌦️' },
  55: { description: 'Dense Drizzle', icon: CloudRain, emoji: '🌦️' },
  61: { description: 'Slight Rain', icon: CloudRain, emoji: '🌧️' },
  63: { description: 'Moderate Rain', icon: CloudRain, emoji: '🌧️' },
  65: { description: 'Heavy Rain', icon: CloudRain, emoji: '🌧️' },
  71: { description: 'Slight Snowfall', icon: Cloud, emoji: '🌨️' },
  73: { description: 'Moderate Snowfall', icon: Cloud, emoji: '🌨️' },
  75: { description: 'Heavy Snowfall', icon: Cloud, emoji: '🌨️' },
  80: { description: 'Slight Rain showers', icon: CloudRain, emoji: '🌦️' },
  81: { description: 'Moderate Rain showers', icon: CloudRain, emoji: '🌧️' },
  82: { description: 'Violent Rain showers', icon: CloudRain, emoji: '⛈️' },
  95: { description: 'Thunderstorm', icon: Zap, emoji: '⛈️' },
  96: { description: 'Thunderstorm with slight hail', icon: Zap, emoji: '⛈️' },
  99: { description: 'Thunderstorm with heavy hail', icon: Zap, emoji: '⛈️' },
};

// Moved outside the component as it's a pure function and doesn't depend on component state/props.
// This prevents it from being recreated on every render and stabilizes the dependency for useMemo.
const getWeatherInfo = (code: number) => {
  return WMO_CODES[code] || { description: 'Clear sky', icon: Sun, emoji: '☀️' };
};

const WeatherAlerts = () => {
  const [selectedTab, setSelectedTab] = useState("current");
  const [cityInput, setCityInput] = useState("");
  const {
    weatherData,
    forecastData,
    locationName,
    loading,
    error,
    fetchWeatherByCity,
    useCurrentLocation,
  } = useWeather();

  const alerts = [
    {
      type: "warning",
      title: "Heavy Rain Expected",
      message: "Moderate to heavy rainfall expected tomorrow. Consider protecting sensitive crops.",
      time: "2 hours ago",
      severity: "Medium",
      icon: CloudRain
    },
    {
      type: "info", 
      title: "Ideal Spraying Conditions",
      message: "Low wind speed and optimal humidity for pesticide/fertilizer application.",
      time: "1 hour ago",
      severity: "Low",
      icon: Sun
    },
    {
      type: "critical",
      title: "Frost Warning",
      message: "Temperature may drop below 5°C tonight. Protect sensitive plants.",
      time: "30 minutes ago",
      severity: "High",
      icon: AlertTriangle
    }
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "low": return "bg-success/10 text-success border-success/20";
      case "medium": return "bg-warning/10 text-warning border-warning/20";
      case "high": return "bg-destructive/10 text-destructive border-destructive/20";
      default: return "bg-muted";
    }
  };

  const handleSearch = () => {
    if (cityInput.trim()) {
      fetchWeatherByCity(cityInput);
    }
  };

  const { currentWeather, weeklyForecast, temperatureData } = useMemo(() => {
    if (!weatherData || !forecastData) {
      return { currentWeather: null, weeklyForecast: [], temperatureData: [] };
    }

    const current = {
      temperature: Math.round(weatherData.main.temp),
      condition: weatherData.weather[0].description.replace(/\b\w/g, (l: string) => l.toUpperCase()),
      humidity: weatherData.main.humidity,
      windSpeed: weatherData.wind.speed,
      visibility: weatherData.visibility / 1000, // meters to km
      uvIndex: forecastData.daily.uv_index_max[1], // Today's UV index from forecast
      feelsLike: Math.round(weatherData.main.feels_like),
      icon: getWeatherInfo(forecastData.current.weather_code).icon,
    };

    const forecast = forecastData.daily.time.slice(1, 8).map((date: string, i: number) => ({
      day: new Date(date).toLocaleDateString('en-US', { weekday: 'short' }),
      high: Math.round(forecastData.daily.temperature_2m_max[i + 1]),
      low: Math.round(forecastData.daily.temperature_2m_min[i + 1]),
      condition: getWeatherInfo(forecastData.daily.weather_code[i + 1]).description,
      rain: forecastData.daily.precipitation_probability_max[i + 1],
      icon: getWeatherInfo(forecastData.daily.weather_code[i + 1]).emoji,
    }));

    const temp = forecastData.hourly.time.slice(0, 24).map((time: string, i: number) => ({
      time: new Date(time).toLocaleTimeString('en-US', { hour: 'numeric', hour12: true }),
      temp: Math.round(forecastData.hourly.temperature_2m[i]),
    })).filter((_: any, i: number) => i % 3 === 0);

    return { currentWeather: current, weeklyForecast: forecast, temperatureData: temp };
  }, [weatherData, forecastData]);

  if (loading) {
    return <div className="flex justify-center items-center h-96"><Loader2 className="h-8 w-8 animate-spin" /> <span className="ml-2">Loading Weather Data...</span></div>;
  }

  return (
    <div className="space-y-6 lg:pl-4 pt-6">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-gradient-to-r from-primary to-accent rounded-lg">
          <CloudRain className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Weather & Alerts</h1>
          <p className="text-muted-foreground">Stay informed with real-time weather updates and farming alerts</p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error Fetching Weather</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card className="border-0 shadow-card-shadow">
        <CardHeader>
            <CardTitle>Location</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row gap-4 items-center">
            <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input 
                    placeholder="Enter a city name..." 
                    value={cityInput}
                    onChange={(e) => setCityInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="pl-10"
                />
            </div>
            <Button onClick={handleSearch}>Search</Button>
            <Button variant="outline" onClick={useCurrentLocation}><MapPin className="h-4 w-4 mr-2" />Use Current Location</Button>
        </CardContent>
      </Card>

      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="grid w-fit grid-cols-3">
          <TabsTrigger value="current">Current</TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="current" className="space-y-6">
        {currentWeather && (
          <>
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Current Weather */}
            <Card className="border-0 shadow-card-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Current Weather</CardTitle>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    <span>{locationName}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-4">                    
                    <currentWeather.icon className="h-8 w-8 text-primary" />
                    <div>
                      <p className="text-4xl font-bold">{currentWeather.temperature}°C</p>
                      <p className="text-muted-foreground">{currentWeather.condition}</p>
                      <p className="text-sm text-muted-foreground">Feels like {currentWeather.feelsLike}°C</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
                    <Droplets className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm text-muted-foreground">Humidity</p>
                      <p className="font-semibold">{currentWeather.humidity}%</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
                    <Wind className="h-5 w-5 text-accent" />
                    <div>
                      <p className="text-sm text-muted-foreground">Wind Speed</p>
                      <p className="font-semibold">{currentWeather.windSpeed} km/h</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
                    <Eye className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Visibility</p>
                      <p className="font-semibold">{currentWeather.visibility} km</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
                    <Sun className="h-5 w-5 text-warning" />
                    <div>
                      <p className="text-sm text-muted-foreground">UV Index</p>
                      <p className="font-semibold">{currentWeather.uvIndex}/10</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Today's Temperature Chart */}
            <Card className="border-0 shadow-card-shadow">
              <CardHeader>
                <CardTitle>Today's Temperature</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={temperatureData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone" 
                      dataKey="temp" 
                      stroke="hsl(var(--primary))" 
                      strokeWidth={3}
                      dot={{ fill: 'hsl(var(--primary))', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Farming Conditions */}
          <Card className="border-0 shadow-card-shadow">
            <CardHeader>
              <CardTitle>Farming Conditions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-success/10 rounded-lg border border-success/20">
                  <div className="text-2xl mb-2">🌱</div>
                  <h4 className="font-medium text-success mb-1">Excellent for Planting</h4>
                  <p className="text-xs text-muted-foreground">Soil moisture and temperature are ideal</p>
                </div>

                <div className="text-center p-4 bg-warning/10 rounded-lg border border-warning/20">
                  <div className="text-2xl mb-2">💧</div>
                  <h4 className="font-medium text-warning mb-1">Moderate for Irrigation</h4>
                  <p className="text-xs text-muted-foreground">Consider reducing water due to humidity</p>
                </div>

                <div className="text-center p-4 bg-primary/10 rounded-lg border border-primary/20">
                  <div className="text-2xl mb-2">🚜</div>
                  <h4 className="font-medium text-primary mb-1">Good for Field Work</h4>
                  <p className="text-xs text-muted-foreground">Weather suitable for machinery operation</p>
                </div>
              </div>
            </CardContent>
          </Card>
          </>
        )}
        </TabsContent>

        <TabsContent value="forecast" className="space-y-6">
          <Card className="border-0 shadow-card-shadow">
            <CardHeader>
              <CardTitle>7-Day Weather Forecast</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {weeklyForecast && weeklyForecast.map((day, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl">{day.icon}</div>
                      <div>
                        <p className="font-medium">{day.day}</p>
                        <p className="text-sm text-muted-foreground">{day.condition}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground">High/Low</p>
                        <p className="font-semibold">{day.high}°/{day.low}°</p>
                      </div>

                      <div className="text-center">
                        <p className="text-xs text-muted-foreground">Rain</p>
                        <div className="flex items-center space-x-2">
                          <Progress value={day.rain} className="w-16 h-2" />
                          <span className="text-sm font-medium">{day.rain}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            <Card className="border-0 shadow-card-shadow">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Bell className="h-5 w-5" />
                  <span>Active Alerts</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {alerts.map((alert, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}>
                    <div className="flex items-start space-x-3">
                      <alert.icon className="h-5 w-5 mt-0.5" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-medium">{alert.title}</h4>
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{alert.message}</p>
                        <p className="text-xs text-muted-foreground">{alert.time}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-0 shadow-card-shadow">
              <CardHeader>
                <CardTitle>Alert Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div>
                      <p className="font-medium">Rain Alerts</p>
                      <p className="text-sm text-muted-foreground">Get notified about rainfall predictions</p>
                    </div>
                    <Button size="sm" variant="outline">Enabled</Button>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div>
                      <p className="font-medium">Temperature Warnings</p>
                      <p className="text-sm text-muted-foreground">Alerts for extreme temperatures</p>
                    </div>
                    <Button size="sm" variant="outline">Enabled</Button>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div>
                      <p className="font-medium">Frost Alerts</p>
                      <p className="text-sm text-muted-foreground">Early warning for frost conditions</p>
                    </div>
                    <Button size="sm" variant="outline">Enabled</Button>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div>
                      <p className="font-medium">Wind Speed Alerts</p>
                      <p className="text-sm text-muted-foreground">High wind speed notifications</p>
                    </div>
                    <Button size="sm" variant="secondary">Disabled</Button>
                  </div>
                </div>

                <Button className="w-full">
                  <Bell className="mr-2 h-4 w-4" />
                  Customize Alerts
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

      </Tabs>
    </div>
  );
};

export default WeatherAlerts;