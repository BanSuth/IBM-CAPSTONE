// tag::copyright[]
/*******************************************************************************
 * Copyright (c) 2022, 2023 IBM Corporation and others.
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License 2.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-2.0/
 *
 * SPDX-License-Identifier: EPL-2.0
 *******************************************************************************/
// end::copyright[]
package io.openliberty.guides.system;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.OperatingSystemMXBean;
import java.util.Calendar;
import java.util.HashSet;
import java.util.Set;
import java.util.logging.Logger;

import com.pi4j.Pi4J;
import com.pi4j.context.Context;
import com.pi4j.exception.Pi4JException;
import com.pi4j.io.gpio.digital.DigitalInput;
import com.pi4j.io.gpio.digital.DigitalOutput;
import com.pi4j.io.gpio.digital.DigitalOutputConfigBuilder;
import com.pi4j.io.gpio.digital.DigitalState;
import jakarta.json.Json;
import jakarta.json.JsonObject;
import jakarta.json.JsonObjectBuilder;
import jakarta.websocket.CloseReason;
import jakarta.websocket.OnClose;
import jakarta.websocket.OnError;
import jakarta.websocket.OnMessage;
import jakarta.websocket.OnOpen;
import jakarta.websocket.Session;
import jakarta.websocket.server.ServerEndpoint;

// tag::serverEndpoint[]
@ServerEndpoint(value = "/")
// end::serverEndpoint[]
public class SystemService {

    private static Logger logger = Logger.getLogger(SystemService.class.getName());

    private Context pi4j;
    public DigitalOutput motorEnableA, motorEnableB, input1, input2, input3, input4;
    private static final int ENABLE_A = 14;
    private static final int INPUT_1 = 15;
    private static final int INPUT_2 = 13;
    private static final int INPUT_3 = 2;
    private static final int INPUT_4 = 0;
    private static final int ENABLE_B = 12;
    private static final int BATTERY_PIN = 0;
    private static final int ROVER_HEADLIGHTS = 5;
    private static final int ROVER_SPEED = 220;
    private static final int ROVER_FW_BW_SPEED = 135;
    private static final int ROVER_LR_SPEED = 200;
    private static final int TURN_COEFFICIENT = 45;
    private static boolean isColorDetected = false;
    private static String colorDetected = "NC";
    private static int roverHeadlights = 5;
    private static double batteryVoltCoef = 1.98;
    private static double cutoffVolt = 5.5;
    private static double batteryVolt = 7.2;

    private static boolean isGameStarted = false;

    private static String connected = "";
    private static int wsNum = 0;
    private static final int SENSOR_PIN = 1; // Replace with the actual sensor pin

    private static final int MOTOR_ENABLE_A_PIN = 17;
    private static final int MOTOR_ENABLE_B_PIN = 16;
    private static final int MOTOR_INPUT_1_PIN = 23;
    private static final int MOTOR_INPUT_2_PIN = 24;
    private static final int MOTOR_INPUT_3_PIN = 20;
    private static final int MOTOR_INPUT_4_PIN = 21;


    private DigitalOutput enableA;

    private DigitalOutput enableB;
    private DigitalInput batteryPin;
    private static String roverConnMsg = "Rover Connected";

    private static double actualVoltage = 0.0;
    private static int batteryPercent = 0;
    private static Set<Session> sessions = new HashSet<>();


    public SystemService() {
        try {
            // Initialize Pi4J with auto context
            pi4j = Pi4J.newAutoContext();

            // Setting Up GPIO Pins with error handling
            motorEnableA = pi4j.create(buildDigitalOutputConfig(pi4j, MOTOR_ENABLE_A_PIN));
            motorEnableB = pi4j.create(buildDigitalOutputConfig(pi4j, MOTOR_ENABLE_B_PIN));
            input1 = pi4j.create(buildDigitalOutputConfig(pi4j, MOTOR_INPUT_1_PIN));
            input2 = pi4j.create(buildDigitalOutputConfig(pi4j, MOTOR_INPUT_2_PIN));
            input3 = pi4j.create(buildDigitalOutputConfig(pi4j, MOTOR_INPUT_3_PIN));
            input4 = pi4j.create(buildDigitalOutputConfig(pi4j, MOTOR_INPUT_4_PIN));
        } catch (Pi4JException e) {
            System.err.println("Error initializing GPIO pins: " + e.getMessage());
        }
    }

    public static DigitalOutputConfigBuilder buildDigitalOutputConfig(Context pi4j, int address) {
        return DigitalOutput.newConfigBuilder(pi4j)
                .address(address)
                .shutdown(DigitalState.LOW) // Ensure pin is LOW on shutdown for safety
                .initial(DigitalState.LOW)
                .provider("linuxfs-digital-output");
    }
    // tag::sendToAllSessionseMethod[]
    public static void sendToAllSessions(JsonObject systemLoad) {
        for (Session session : sessions) {
            try {
                session.getBasicRemote().sendObject(systemLoad);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
    // end::sendToAllSessionseMethod[]

    // tag::onOpenMethod[]
    // tag::onOpen[]
    @OnOpen
    // end::onOpen[]
    public void onOpen(Session session) throws IOException {
        logger.info("Server connected to session: " + session.getId());
        sessions.add(session);
        String connected = roverConnMsg + "|" + actualVoltage + "|" + batteryPercent;

        session.getBasicRemote().sendText(connected);
        System.out.println("<WSC>");
    }
    // end::onOpenMethod[]

    // tag::onMessageMethod[]
    // tag::onMessage[]
    @OnMessage
    // end::onMessage[]
    public void onMessage(String message, Session session) {
        logger.info("Server received message \"" + message + "\" "
                    + "from session: " + session.getId());
        switch (message) {
            case "1":
                isGameStarted=true;
                break;
            case "F":
                moveForward();
                break;
            case "B":
                moveReverse();
                break;
            case "L":
                moveLeft();
                break;
            case "R":
                moveRight();
                break;
            case "S": // New case for stopping the motors
                stopMotors();
                break;
            default:
                System.out.println("Unknown command: " + message);
                break;
        }
    }
    // end::onMessageMethod[]
    public void moveForward() {
        // Logic to control GPIO pins for moving forward
        System.out.println("Forward Being Called");
        if(isGameStarted) {

            motorEnableA.high();
            motorEnableB.high();
            input1.high();
            input2.low();
            input3.high();
            input4.low();
        }
    }
    // Reverse movement
    private void moveReverse() {
        System.out.println("Reverse Being Called");
        if(isGameStarted) {
            motorEnableA.high();
            motorEnableB.high();
            input1.low(); // Reverse polarity compared to forward
            input2.high();
            input3.low(); // Reverse polarity compared to forward
            input4.high();
        }
    }

    // Move left
    private void moveLeft() {
        System.out.println("Left Being Called");
        if(isGameStarted) {
            motorEnableA.high();
            motorEnableB.high();
            input1.low(); // Stop right motor, drive left motor
            input2.high();
            input3.high(); // Drive left motor
            input4.low();
        }
    }

    // Move right
    private void moveRight() {
        System.out.println("Right Being Called");
        if(isGameStarted) {
            motorEnableA.high();
            motorEnableB.high();
            input1.high(); // Drive right motor
            input2.low();
            input3.low(); // Stop left motor, drive right motor
            input4.high();
        }
    }

    // Method to stop the motors
    private void stopMotors() {
        System.out.println("Stopping Motors");
        if(isGameStarted) {
            motorEnableA.low(); // Turn off motor A
            motorEnableB.low(); // Turn off motor B
            // Optionally, ensure all input pins are set to LOW to ensure a clean stop
            input1.low();
            input2.low();
            input3.low();
            input4.low();
        }
    }
    // tag::onCloseMethod[]
    // tag::onClose[]
    @OnClose
    // end::onClose[]
    public void onClose(Session session, CloseReason closeReason) {
        logger.info("Session " + session.getId()
                    + " was closed with reason " + closeReason.getCloseCode());
        sessions.remove(session);
        System.out.println("<GE>");
        stopMotors();
        isGameStarted = false;
    }
    // end::onCloseMethod[]

    // tag::onError[]
    @OnError
    // end::onError[]
    public void onError(Session session, Throwable throwable) {
        logger.info("WebSocket error for " + session.getId() + " "
                    + throwable.getMessage());
    }
}
