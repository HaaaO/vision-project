#!/usr/bin/env python3.8
import actionlib
import datetime
import os
import rospy
import schedule

from controllers import VisionProjectDelegator
from data_structures import state_database

from ros_vision_interaction.msg import StartInteractionAction, StartInteractionGoal
from std_msgs.msg import Bool

START_INTERACTION_ACTION_NAME = "vision_project/start_interaction"


class RosVisionProjectDelegator:

    def __init__(
            self,
            vision_project_delegator,
            is_record_topic='data_capture/is_record',
            start_interaction_action_name=START_INTERACTION_ACTION_NAME,
    ):
        self._delegator = vision_project_delegator

        # action client to start interaction
        self._start_interaction_client = actionlib.SimpleActionClient(
            start_interaction_action_name,
            StartInteractionAction
        )

        # ROS publishers and subscribers
        self._is_record_publisher = rospy.Publisher(is_record_topic, Bool, queue_size=1)

        # update scheduler
        self._scheduler = schedule.Scheduler()
        self._scheduler.every(10).seconds.do(self.update)

        self._is_debug = rospy.get_param(
            "vision-project/controllers/is_debug",
            False
        )

    def run_schedulers_once(self):
        self._scheduler.run_pending()

    def update(self):
        rospy.loginfo("Running update")
        interaction_type = self._delegator.determine_interaction_type()
        if interaction_type is not None:
            rospy.loginfo("Delegating interaction: {}".format(interaction_type))
            self.delegate_interaction(interaction_type)

    def delegate_interaction(self, interaction_type):
        self._start_interaction_client.wait_for_server()

        start_interaction_goal = StartInteractionGoal()
        start_interaction_goal.type = interaction_type

        if not self._is_debug:
            # TODO: add a feedback callback
            rospy.loginfo("Sending goal to start interaction")
            self._start_interaction_client.send_goal(start_interaction_goal)
            self._start_interaction_client.wait_for_result()

        return


if __name__ == "__main__":

    rospy.init_node("vision_project_delegator")

    is_run_demo_interaction = rospy.get_param("vision-project/is_run_demo_interaction")

    vision_project_delegator = VisionProjectDelegator(
        mongodb_statedb=state_database,
        is_run_demo_interaction=is_run_demo_interaction,
        is_clear_state=True,
    )

    ros_vision_project_delegator = RosVisionProjectDelegator(vision_project_delegator)

    while not rospy.is_shutdown():
        ros_vision_project_delegator.run_schedulers_once()
        rospy.sleep(1)
