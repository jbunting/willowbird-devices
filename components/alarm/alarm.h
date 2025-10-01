// alarm.h
#pragma once
#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "esphome/components/time/real_time_clock.h"
#include "esphome/components/rtttl/rtttl.h"
#include "esphome/components/binary_sensor/binary_sensor.h"

namespace esphome {
namespace alarm {

class Alarm : public Component {
 public:
  void set_time_component(time::RealTimeClock *time) { this->time_ = time; }
  void set_rtttl(rtttl::RTTTL *rtttl) { this->rtttl_ = rtttl; }

  void set_alarm_time(uint8_t hour, uint8_t minute) {
    this->alarm_hour_ = hour;
    this->alarm_minute_ = minute;
  }
  void set_rtttl_sequence(const std::string &seq) { this->sequence_ = seq; }

  void set_condition(std::function<bool()> condition) { this->condition_ = condition; }

  // Actions
  void stop();
  void snooze(uint32_t ms);   // pass in duration in milliseconds
  void unsnooze();

  void setup() override;
  void loop() override {}  // unused

  // Binary sensors
  binary_sensor::BinarySensor *active_sensor{nullptr};
  binary_sensor::BinarySensor *snoozed_sensor{nullptr};

 protected:
  void trigger_alarm_();
  void set_active_state_(bool playing, bool snoozed);

  time::RealTimeClock *time_{nullptr};
  rtttl::RTTTL *rtttl_{nullptr};

  uint8_t alarm_hour_{0};
  uint8_t alarm_minute_{0};

  std::string sequence_;
  std::function<bool()> condition_;

  bool playing_{false};
  bool snoozed_{false};
  ESPPreferenceObject snooze_timer_;
};

}  // namespace alarm
}  // namespace esphome

class AlarmStopAction : public Action {
 public:
  AlarmStopAction(Alarm *parent) : parent_(parent) {}
  void play(Ts... x) { this->parent_->stop(); }
 protected:
  Alarm *parent_;
};

class AlarmSnoozeAction : public Action {
 public:
  AlarmSnoozeAction(Alarm *parent, uint32_t duration) : parent_(parent), duration_(duration) {}
  void play(Ts... x) { this->parent_->snooze(this->duration_); }
 protected:
  Alarm *parent_;
  uint32_t duration_;
};

class AlarmUnsnoozeAction : public Action {
 public:
  AlarmUnsnoozeAction(Alarm *parent) : parent_(parent) {}
  void play(Ts... x) { this->parent_->unsnooze(); }
 protected:
  Alarm *parent_;
};
