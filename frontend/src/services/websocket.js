const WS_URL = "ws://localhost:8000/ws/dashboard";


class DashboardSocket {


    constructor(){

        this.socket = null;
        this.listeners = [];

    }



    connect(){

        if(
            this.socket &&
            this.socket.readyState === WebSocket.OPEN
        ){
            return;
        }


        this.socket = new WebSocket(WS_URL);



        this.socket.onopen = ()=>{

            console.log(
                "🟢 Dashboard WebSocket connected"
            );

        };



        this.socket.onmessage = (event)=>{


            const message = JSON.parse(
                event.data
            );


            console.log(
                "📡 Received:",
                message
            );


            this.listeners.forEach(
                callback => callback(message)
            );


        };



        this.socket.onerror = (error)=>{

            console.error(
                "WebSocket Error:",
                error
            );

        };



        this.socket.onclose = ()=>{

            console.log(
                "🔴 Dashboard WebSocket disconnected"
            );

        };


    }




    subscribe(callback){

        this.listeners.push(callback);



        return ()=>{

            this.listeners =
            this.listeners.filter(
                item => item !== callback
            );

        };

    }



    disconnect(){

        if(this.socket){

            this.socket.close();

        }

    }

}


export const dashboardSocket =
new DashboardSocket();